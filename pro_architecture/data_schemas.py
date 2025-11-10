#!/usr/bin/env python3
"""
Data schemas for all Mandate Wizard card types.
Provides validation and standardization for all data ingested into the knowledge base.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal, Dict, Any
from datetime import date

class Source(BaseModel):
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    date: Optional[date] = None

class ExecutiveCard(BaseModel):
    id: str = Field(..., description="Unique ID (firstname_lastname)")
    type: Literal["executive"] = "executive"
    name: str
    title: str
    company: str
    region: Literal["Global", "MENA", "LATAM", "Europe", "UK", "US"]
    bio: Optional[str] = None
    mandate: Optional[str] = None
    recent_greenlights: List[str] = []
    reports_to: Optional[str] = None
    team_members: List[str] = []
    contact_hints: Optional[str] = None
    genres: List[str] = []
    formats: List[str] = []
    budget_range: Optional[str] = None
    updated: date
    sources: List[Source] = []

class MandateCard(BaseModel):
    id: str = Field(..., description="Unique ID (mandate_platform_dept_year)")
    type: Literal["mandate"] = "mandate"
    platform: str
    department: str
    executive: Optional[str] = None
    summary: str
    genres: List[str] = []
    formats: List[str] = []
    budget_range: Optional[str] = None
    key_requirements: List[str] = []
    recent_examples: List[str] = []
    updated: date
    sources: List[Source] = []

class CompanyDeal(BaseModel):
    platform: str
    type: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    value: Optional[str] = None

class CompanyCard(BaseModel):
    id: str = Field(..., description="Unique ID (company_name)")
    type: Literal["company"] = "company"
    name: str
    founder: Optional[str] = None
    key_people: List[str] = []
    deals: List[CompanyDeal] = []
    recent_projects: List[str] = []
    focus_areas: List[str] = []
    submission_policy: Optional[str] = None
    updated: date
    sources: List[Source] = []

class ProcessCard(BaseModel):
    id: str = Field(..., description="Unique ID (process_title)")
    type: Literal["process"] = "process"
    title: str
    summary: str
    steps: List[str] = []
    tips: List[str] = []
    common_mistakes: List[str] = []
    updated: date
    sources: List[Source] = []

class NewsDealCard(BaseModel):
    id: str = Field(..., description="Unique ID (news_title_date)")
    type: Literal["news"] = "news"
    title: str
    date: date
    platform: Optional[str] = None
    production_company: Optional[str] = None
    executives: List[str] = []
    genre: Optional[str] = None
    deal_type: Optional[str] = None
    budget: Optional[str] = None
    key_talent: List[str] = []
    sources: List[Source] = []

class MetricsCard(BaseModel):
    id: str = Field(..., description="Unique ID (metrics_title_date)")
    type: Literal["metrics"] = "metrics"
    title: str
    platform: str
    metric_type: str
    data: Dict[str, Any]
    insights: str
    updated: date
    sources: List[Source] = []

# Validator function
def validate_card(data: dict) -> dict:
    card_type = data.get("type")
    if card_type == "executive":
        return ExecutiveCard(**data).dict()
    elif card_type == "mandate":
        return MandateCard(**data).dict()
    elif card_type == "company":
        return CompanyCard(**data).dict()
    elif card_type == "process":
        return ProcessCard(**data).dict()
    elif card_type == "news":
        return NewsDealCard(**data).dict()
    elif card_type == "metrics":
        return MetricsCard(**data).dict()
    else:
        raise ValueError(f"Unknown card type: {card_type}")
