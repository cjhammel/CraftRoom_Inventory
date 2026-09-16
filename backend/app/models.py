from sqlalchemy import Column, Integer, String
from app.database import Base


class Stamp(Base):
    __tablename__ = "stamp"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    brand_name = Column(String, nullable=True)
    product_type = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    theme = Column(String, nullable=True)
    shape_descriptor = Column(String, nullable=True)
    sentiments = Column(String, nullable=True)
    location = Column(String, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "product_name": self.product_name,
            "brand_name": self.brand_name,
            "product_type": self.product_type,
            "image_url": self.image_url,
            "theme": self.theme,
            "shape_descriptor": self.shape_descriptor,
            "sentiments": self.sentiments,
            "location": self.location,
        }
