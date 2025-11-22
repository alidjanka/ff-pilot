from pydantic import BaseModel, Field
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Config(BaseModel):
    openai_key: str = os.getenv("OPENAI_KEY")
    input_file: str = Field(default=os.path.join("data","Coding_Challenge_Sales_and_Price_data.csv"), description="Path to sales CSV")
    article_dir: str = Field(default=os.path.join("data","articles"), description="Directory with article files")
    model_type: str = Field(default="linear")
    output_dir: str = Field(default='outputs', description="Output folder")
    blacklist_products: Optional[List[str]] = None
    scenario: Optional[str] = "standard"