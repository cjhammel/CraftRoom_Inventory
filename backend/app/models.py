from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Location(Base):
    __tablename__ = "location"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cabinet = Column(String, nullable=True)
    shelf = Column(String, nullable=True)
    bin = Column(String, nullable=True)

    products = relationship("Stamp", back_populates="storage_location")

    def display_name(self):
        parts = [part for part in (self.cabinet, self.shelf, self.bin) if part]
        return " / ".join(parts) if parts else None


class Stamp(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_number = Column(String, nullable=True)
    product_name = Column(String, nullable=False)
    brand_name = Column(String, nullable=True)
    product_type = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    theme = Column(String, nullable=True)
    shape_descriptor = Column(String, nullable=True)
    sentiments = Column(String, nullable=True)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=True, index=True)

    storage_location = relationship("Location", back_populates="products")

    @property
    def location(self):
        return self.storage_location.display_name() if self.storage_location else None

    @property
    def cabinet(self):
        return self.storage_location.cabinet if self.storage_location else None

    @property
    def shelf(self):
        return self.storage_location.shelf if self.storage_location else None

    @property
    def bin(self):
        return self.storage_location.bin if self.storage_location else None

    def to_dict(self):
        return {
            "id": self.id,
            "item_number": self.item_number,
            "product_name": self.product_name,
            "brand_name": self.brand_name,
            "product_type": self.product_type,
            "image_url": self.image_url,
            "theme": self.theme,
            "shape_descriptor": self.shape_descriptor,
            "sentiments": self.sentiments,
            "location_id": self.location_id,
            "location": self.location,
            "cabinet": self.cabinet,
            "shelf": self.shelf,
            "bin": self.bin,
        }
