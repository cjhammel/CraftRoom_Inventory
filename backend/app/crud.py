from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Location, Stamp
from typing import Optional, List, Dict, Any


def _clean_location_part(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _normalize_location_data(location_data: Any) -> Dict[str, Optional[str]]:
    if isinstance(location_data, dict):
        return {
            "cabinet": _clean_location_part(location_data.get("cabinet")),
            "shelf": _clean_location_part(location_data.get("shelf")),
            "bin": _clean_location_part(location_data.get("bin")),
        }
    return {
        "cabinet": _clean_location_part(location_data),
        "shelf": None,
        "bin": None,
    }


def _get_or_create_location(db: Session, location_data: Any) -> Optional[Location]:
    values = _normalize_location_data(location_data)
    if not any(values.values()):
        return None

    location = db.query(Location).filter_by(**values).first()
    if location:
        return location

    location = Location(**values)
    db.add(location)
    db.flush()
    return location


def get_location(db: Session, location_id: int) -> Optional[Location]:
    return db.query(Location).filter(Location.id == location_id).first()


def get_locations(db: Session) -> List[Location]:
    return (
        db.query(Location)
        .order_by(Location.cabinet.asc(), Location.shelf.asc(), Location.bin.asc())
        .all()
    )


def create_location(db: Session, location_data: Dict[str, Optional[str]]) -> Location:
    values = _normalize_location_data(location_data)
    location = Location(**values)
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def update_location(
    db: Session,
    location_id: int,
    location_data: Dict[str, Optional[str]],
) -> Optional[Location]:
    location = get_location(db, location_id)
    if not location:
        return None

    values = _normalize_location_data(location_data)
    for key, value in values.items():
        setattr(location, key, value)

    db.commit()
    db.refresh(location)
    return location


def get_stamp(db: Session, stamp_id: int) -> Optional[Stamp]:
    return db.query(Stamp).filter(Stamp.id == stamp_id).first()


def get_stamps(
    db: Session,
    search: Optional[str] = None,
    brand_name: Optional[str] = None,
    product_type: Optional[str] = None,
    theme: Optional[str] = None,
    location: Optional[str] = None,
    sentiments: Optional[str] = None,
) -> List[Stamp]:
    query = db.query(Stamp)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Stamp.product_name.ilike(search_term))
            | (Stamp.brand_name.ilike(search_term))
            | (Stamp.item_number.ilike(search_term))
        )

    if brand_name:
        query = query.filter(Stamp.brand_name.ilike(f"%{brand_name}%"))

    if product_type:
        query = query.filter(Stamp.product_type.ilike(f"%{product_type}%"))

    if theme:
        query = query.filter(Stamp.theme.ilike(f"%{theme}%"))

    if location:
        location_term = f"%{location}%"
        query = query.join(Stamp.storage_location).filter(
            or_(
                Location.cabinet.ilike(location_term),
                Location.shelf.ilike(location_term),
                Location.bin.ilike(location_term),
            )
        )

    if sentiments:
        sentiment_terms = [t.strip().lower() for t in sentiments.split() if t.strip()]
        if sentiment_terms:
            sentiment_conditions = [Stamp.sentiments.ilike(f"%{term}%") for term in sentiment_terms]
            query = query.filter(or_(*sentiment_conditions))

    return query.all()


def create_stamp(db: Session, stamp_data: Dict[str, Any]) -> Stamp:
    location_data = stamp_data.pop("location", None)
    if location_data is not None:
        location = _get_or_create_location(db, location_data)
        stamp_data["location_id"] = location.id if location else None

    db_stamp = Stamp(**stamp_data)
    db.add(db_stamp)
    db.commit()
    db.refresh(db_stamp)
    return db_stamp


def update_stamp(db: Session, stamp_id: int, stamp_data: Dict[str, Any]) -> Optional[Stamp]:
    db_stamp = get_stamp(db, stamp_id)
    if not db_stamp:
        return None

    if "location" in stamp_data:
        location = _get_or_create_location(db, stamp_data.pop("location"))
        db_stamp.location_id = location.id if location else None

    for key, value in stamp_data.items():
        if key == "location_id" or value is not None:
            setattr(db_stamp, key, value)

    db.commit()
    db.refresh(db_stamp)
    return db_stamp


def delete_stamp(db: Session, stamp_id: int) -> bool:
    db_stamp = get_stamp(db, stamp_id)
    if not db_stamp:
        return False
    db.delete(db_stamp)
    db.commit()
    return True
