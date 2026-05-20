"""Whitelist service."""

import uuid
import re
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.enums import WhitelistType, WhitelistStatus
from app.db.session import get_db_context
from app.models import Whitelist, User


class WhitelistService:
    """Whitelist service for target validation."""

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL for comparison."""
        try:
            parsed = urlparse(url)
            # Remove default ports
            netloc = parsed.netloc
            if parsed.scheme == 'http' and ':80' in netloc:
                netloc = netloc.replace(':80', '')
            elif parsed.scheme == 'https' and ':443' in netloc:
                netloc = netloc.replace(':443', '')
            # Lowercase domain
            if '@' not in netloc:
                netloc = netloc.lower()
            # Build normalized URL
            normalized = f"{parsed.scheme}://{netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized.rstrip('/')
        except Exception:
            return url.lower().rstrip('/')

    @staticmethod
    def normalize_domain(domain: str) -> str:
        """Normalize domain for comparison."""
        domain = domain.lower().strip()
        # Remove protocol if present
        if '://' in domain:
            domain = urlparse(domain).netloc or urlparse(domain).path
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

    @staticmethod
    def normalize_ip(ip: str) -> str:
        """Normalize IP address."""
        return ip.strip().lower()

    @staticmethod
    def normalize_repo(repo: str) -> str:
        """Normalize repository URL."""
        repo = repo.lower().strip()
        # Remove .git suffix
        if repo.endswith('.git'):
            repo = repo[:-4]
        return repo.rstrip('/')

    @staticmethod
    def normalize_target(target: str, target_type: str) -> str:
        """Normalize target based on type."""
        normalizers = {
            WhitelistType.URL.value: WhitelistService.normalize_url,
            WhitelistType.DOMAIN.value: WhitelistService.normalize_domain,
            WhitelistType.IP.value: WhitelistService.normalize_ip,
            WhitelistType.REPO.value: WhitelistService.normalize_repo,
        }
        normalizer = normalizers.get(target_type)
        if normalizer:
            return normalizer(target)
        return target.lower().strip()

    @staticmethod
    def extract_domain_from_url(url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            # Remove port
            if ':' in domain:
                domain = domain.rsplit(':', 1)[0]
            return domain.lower()
        except Exception:
            return url.lower()

    @staticmethod
    def check_whitelist(db: Session, target: str) -> tuple[bool, str | None]:
        """
        Check if target is in whitelist.
        Returns (allowed, matched_whitelist_id).
        """
        # Normalize the target
        normalized_target = target.lower().strip()

        # Get all enabled whitelists
        all_whitelists = db.query(Whitelist).filter(
            Whitelist.status == WhitelistStatus.ENABLED.value,
        ).all()

        for wl in all_whitelists:
            wl_normalized = wl.target_normalized.lower() if wl.target_normalized else ""

            if wl.target_type == WhitelistType.URL.value:
                # URL whitelist: exact match or domain match
                if normalized_target == wl_normalized:
                    return True, wl.id
                # Also match if domain matches
                target_domain = WhitelistService.extract_domain_from_url(normalized_target)
                wl_domain = wl_normalized.split('://')[-1] if '://' in wl_normalized else wl_normalized
                if target_domain == wl_domain or target_domain.endswith('.' + wl_domain):
                    return True, wl.id

            elif wl.target_type == WhitelistType.DOMAIN.value:
                # Domain whitelist: exact match or subdomain match
                target_domain = WhitelistService.extract_domain_from_url(normalized_target)
                wl_domain = wl_normalized
                if target_domain == wl_domain or target_domain.endswith('.' + wl_domain):
                    return True, wl.id

            elif wl.target_type == WhitelistType.IP.value:
                # IP whitelist: exact match
                if normalized_target == wl_normalized:
                    return True, wl.id

            elif wl.target_type == WhitelistType.REPO.value:
                # Repo whitelist: exact match
                if normalized_target == wl_normalized:
                    return True, wl.id

        return False, None

    @staticmethod
    def create_whitelist(
        db: Session,
        name: str,
        target_type: str,
        target_value: str,
        created_by: str,
        project: str = None,
    ) -> Whitelist:
        """Create a new whitelist entry."""
        whitelist = Whitelist(
            id=str(uuid.uuid4()),
            name=name,
            target_type=target_type,
            target_value=target_value,
            target_normalized=WhitelistService.normalize_target(target_value, target_type),
            project=project,
            status=WhitelistStatus.ENABLED.value,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(whitelist)
        db.commit()
        db.refresh(whitelist)
        return whitelist

    @staticmethod
    def update_whitelist(
        db: Session,
        whitelist_id: str,
        name: str = None,
        target_type: str = None,
        target_value: str = None,
        project: str = None,
    ) -> Whitelist:
        """Update a whitelist entry."""
        whitelist = db.query(Whitelist).filter(Whitelist.id == whitelist_id).first()
        if not whitelist:
            return None

        if name is not None:
            whitelist.name = name
        if target_type is not None:
            whitelist.target_type = target_type
        if target_value is not None:
            whitelist.target_value = target_value
            whitelist.target_normalized = WhitelistService.normalize_target(target_value, target_type)
        if project is not None:
            whitelist.project = project

        whitelist.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(whitelist)
        return whitelist

    @staticmethod
    def toggle_whitelist(db: Session, whitelist_id: str) -> Whitelist:
        """Toggle whitelist status."""
        whitelist = db.query(Whitelist).filter(Whitelist.id == whitelist_id).first()
        if not whitelist:
            return None

        if whitelist.status == WhitelistStatus.ENABLED.value:
            whitelist.status = WhitelistStatus.DISABLED.value
        else:
            whitelist.status = WhitelistStatus.ENABLED.value

        whitelist.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(whitelist)
        return whitelist

    @staticmethod
    def delete_whitelist(db: Session, whitelist_id: str) -> bool:
        """Delete a whitelist entry."""
        whitelist = db.query(Whitelist).filter(Whitelist.id == whitelist_id).first()
        if not whitelist:
            return False

        db.delete(whitelist)
        db.commit()
        return True

    @staticmethod
    def get_whitelists(
        db: Session,
        name: str = None,
        target_type: str = None,
        status: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Whitelist], int]:
        """Get paginated whitelist entries."""
        query = db.query(Whitelist)

        if name:
            query = query.filter(Whitelist.name.like(f"%{name}%"))
        if target_type:
            query = query.filter(Whitelist.target_type == target_type)
        if status:
            query = query.filter(Whitelist.status == status)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(Whitelist.created_at.desc()).offset(offset).limit(page_size).all()

        return items, total

    @staticmethod
    def get_whitelist_by_id(db: Session, whitelist_id: str) -> Whitelist:
        """Get whitelist by ID."""
        return db.query(Whitelist).filter(Whitelist.id == whitelist_id).first()

    @staticmethod
    def check_whitelist_match(target: str) -> bool:
        """Check if target matches any whitelist entry.

        This is a convenience method that uses a database session.
        Returns True if target is allowed.
        """
        from app.db.session import get_db_context
        with get_db_context() as db:
            allowed, _ = WhitelistService.check_whitelist(db, target)
            return allowed
