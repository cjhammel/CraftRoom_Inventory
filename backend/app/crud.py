from sqlalchemy.orm import Session
from app.models import Stamp
from typing import Optional, List, Dict, Any


def get_stamp(db: Session, stamp_id: int) -> Optional[Stamp]:
    return db.query(Stamp).filter(Stamp.id == stamp_id).first()


def get_stamps(
    db: Session,
    search: Optional[str] = None,
    brand_name: Optional[str] = None,
    product_type: Optional[str] = None,
    location: Optional[str] = None,
    sentiments: Optional[str] = None,
) -> List[Stamp]:
    query = db.query(Stamp)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Stamp.product_name.ilike(search_term)) | (Stamp.brand_name.ilike(search_term))
        )

    if brand_name:
        query = query.filter(Stamp.brand_name.ilike(f"%{brand_name}%"))

    if product_type:
        query = query.filter(Stamp.product_type.ilike(f"%{product_type}%"))

    if location:
        query = query.filter(Stamp.location.ilike(f"%{location}%"))

    if sentiments:
        query = query.filter(Stamp.sentiments.ilike(f"%{sentiments}%"))

    return query.all()


def create_stamp(db: Session, stamp_data: Dict[str, Any]) -> Stamp:
    price_val = stamp_data.get("price")
    if price_val is not None:
        stamp_data["price"] = float(price_val)

    db_stamp = Stamp(**stamp_data)
    db.add(db_stamp)
    db.commit()
    db.refresh(db_stamp)
    return db_stamp


def update_stamp(db: Session, stamp_id: int, stamp_data: Dict[str, Any]) -> Optional[Stamp]:
    db_stamp = get_stamp(db, stamp_id)
    if not db_stamp:
        return None

    price_val = stamp_data.get("price")
    if price_val is not None:
        stamp_data["price"] = float(price_val)

    for key, value in stamp_data.items():
        if value is not None:
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
