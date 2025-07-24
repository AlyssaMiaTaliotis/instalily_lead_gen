from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import logging
import os
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

# Import our custom modules
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.scrapers.events_scraper import EventsScraper
from backend.scrapers.company_scraper import CompanyScraper, enrich_contacts_with_linkedin
from backend.ai_engine.lead_qualifier import LeadQualifier
from backend.ai_engine.outreach_generator import OutreachGenerator
from backend.database.models import Lead, Event, Company

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Instalily AI - Lead Generation System",
    description="Automated lead generation and outreach for DuPont Tedlar Graphics & Signage",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001",    
        "http://127.0.0.1:3001"     
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
events_scraper = EventsScraper()
company_scraper = CompanyScraper()
lead_qualifier = LeadQualifier(OPENAI_API_KEY)
outreach_generator = OutreachGenerator(OPENAI_API_KEY)

# In-memory storage for demo (replace with database in production)
leads_storage = []
events_storage = []
companies_storage = []
outreach_storage = []

# Pydantic models for API requests/responses
class LeadGenerationRequest(BaseModel):
    target_industries: List[str] = ["graphics", "signage", "printing", "advertising"]
    max_leads: int = 50
    min_company_size: str = "medium"
    include_outreach: bool = True

class LeadResponse(BaseModel):
    id: str
    company_name: str
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    qualification_score: float
    industry_alignment: str
    event_context: str
    has_outreach: bool = False

class DashboardStats(BaseModel):
    total_leads: int
    qualified_leads: int
    events_processed: int
    companies_analyzed: int
    outreach_generated: int
    average_qualification_score: float

# Global task status tracking
task_status = {
    "current_task": None,
    "status": "idle",
    "progress": 0,
    "message": "",
    "results": {}
}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Instalily AI Lead Generation System",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "generate_leads": "/api/generate-leads",
            "dashboard": "/api/dashboard",
            "leads": "/api/leads",
            "events": "/api/events",
            "status": "/api/task-status"
        }
    }

@app.post("/api/generate-leads")
async def generate_leads(request: LeadGenerationRequest, background_tasks: BackgroundTasks):
    """Start the automated lead generation process"""
    # Update task status
    global task_status
    task_status = {
        "current_task": "lead_generation",
        "status": "running",
        "progress": 0,
        "message": "Starting lead generation process...",
        "results": {}
    }
    # Run the lead generation process in background
    background_tasks.add_task(
        run_lead_generation_pipeline,
        request.target_industries,
        request.max_leads,
        request.min_company_size,
        request.include_outreach
    )
    return {
        "message": "Lead generation process started",
        "task_id": "lead_generation",
        "status": "initiated",
        "check_status_at": "/api/task-status"
    }

# async def run_lead_generation_pipeline(
#     target_industries: List[str],
#     max_leads: int,
#     min_company_size: str,
#     include_outreach: bool
# ):
#     """Main pipeline for lead generation"""
#     global task_status, leads_storage, events_storage, companies_storage, outreach_storage
#     try:
#         # Step 1: Scrape Events
#         task_status["message"] = "Scraping industry events..."
#         task_status["progress"] = 10
#         events_data = events_scraper.scrape_industry_events(target_industries)
#         events_storage.extend(events_data)
#         logger.info(f"Found {len(events_data)} events")
#         # Step 2: Extract Companies from Events
#         task_status["message"] = "Extracting companies from events..."
#         task_status["progress"] = 30
#         all_companies = []
#         for event in events_data:
#             companies = company_scraper.extract_companies_from_event(event)
#             all_companies.extend(companies)
#         # Deduplicate companies by name (case-insensitive)
#         unique_companies = {}
#         for company in all_companies:
#             name = company.get('name', '').strip().lower() if isinstance(company, dict) else getattr(company, 'name', '').strip().lower()
#             if name and name not in unique_companies:
#                 unique_companies[name] = company
#         all_companies = list(unique_companies.values())

#         companies_storage.extend(all_companies)
#         logger.info(f"Found {len(all_companies)} companies")
#         # Step 3: Enrich Company Data
#         task_status["message"] = "Enriching company data..."
#         task_status["progress"] = 50
#         enriched_companies = []
#         for i, company in enumerate(all_companies[:max_leads]):  # Limit processing
#             enriched = company_scraper.enrich_company_data(company)
#             enriched_companies.append(enriched)
#             # Update progress
#             progress = 50 + (i / min(len(all_companies), max_leads)) * 20
#             task_status["progress"] = int(progress)
#         # Step 4: Qualify Leads
#         task_status["message"] = "Qualifying leads with AI..."
#         task_status["progress"] = 70
#         qualified_leads = []
#         for company in enriched_companies:
#             # Find relevant event context
#             relevant_events = [e for e in events_data if any(
#                 (comp.get('name', '').lower() if isinstance(comp, dict) else getattr(comp, 'name', '').lower()) == company.get('name', '').lower()
#                 for comp in getattr(e, 'companies', [])
#             )]
#             event_context = relevant_events[0] if relevant_events else None
#             # Qualify the lead
#             qualification = lead_qualifier.qualify_lead(company, event_context)
#             if qualification.get('is_qualified', False):
#                 lead_data = {
#                     "id": f"lead_{len(qualified_leads)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
#                     "company_name": company.get('name', ''),
#                     "company_description": company.get('description', ''),
#                     "company_size": company.get('size', ''),
#                     "industry": company.get('industry', ''),
#                     "revenue": company.get('revenue', ''),
#                     "website": company.get('website', ''),
#                     "qualification_score": qualification.get('score', 0),
#                     "qualification_reasons": qualification.get('reasons', []),
#                     "industry_alignment": qualification.get('industry_alignment', ''),
#                     "event_context": event_context.get('name', '') if event_context else '',
#                     "contact_name": company.get('key_contacts', [{}])[0].get('name', ''),
#                     "contact_title": company.get('key_contacts', [{}])[0].get('title', ''),
#                     "contact_linkedin": company.get('key_contacts', [{}])[0].get('linkedin', ''),
#                     "created_at": datetime.now().isoformat()
#                 }
#                 qualified_leads.append(lead_data)
#         leads_storage.extend(qualified_leads)
#         logger.info(f"Qualified {len(qualified_leads)} leads")
#         # Step 5: Generate Outreach (if requested)
#         generated_outreach = []
#         if include_outreach and qualified_leads:
#             task_status["message"] = "Generating personalized outreach..."
#             task_status["progress"] = 80
#             outreach_results = outreach_generator.generate_bulk_outreach(qualified_leads)
#             for result in outreach_results:
#                 if result.get('success', False):
#                     outreach_data = {
#                         "id": f"outreach_{result.get('lead_id', 'unknown')}",
#                         "lead_id": result.get('lead_id'),
#                         "subject_line": result['data']['subject_line'],
#                         "primary_message": result['data']['primary_message'],
#                         "follow_up_sequence": result['data']['follow_up_sequence'],
#                         "personalization_elements": result['data']['personalization_elements'],
#                         "generated_at": result['data']['generated_at'],
#                         "status": "generated"
#                     }
#                     generated_outreach.append(outreach_data)
#             outreach_storage.extend(generated_outreach)
#         # Complete the task
#         task_status = {
#             "current_task": "lead_generation",
#             "status": "completed",
#             "progress": 100,
#             "message": "Lead generation process completed successfully",
#             "results": {
#                 "events_found": len(events_data),
#                 "companies_analyzed": len(all_companies),
#                 "qualified_leads": len(qualified_leads),
#                 "outreach_generated": len(generated_outreach),
#                 "completion_time": datetime.now().isoformat()
#             }
#         }
#         logger.info("Lead generation pipeline completed successfully")
#     except Exception as e:
#         logger.error(f"Error in lead generation pipeline: {str(e)}")
#         task_status = {
#             "current_task": "lead_generation",
#             "status": "error",
#             "progress": 0,
#             "message": f"Error: {str(e)}",
#             "results": {}
#         }

async def run_lead_generation_pipeline(
    target_industries: List[str],
    max_leads: int,
    min_company_size: str,
    include_outreach: bool
):
    """Main pipeline for lead generation"""
    global task_status, leads_storage, events_storage, companies_storage, outreach_storage
    try:
        # Step 1: Scrape Events
        task_status["message"] = "Scraping industry events..."
        task_status["progress"] = 10
        events_data = events_scraper.scrape_industry_events(target_industries)
        events_storage.extend(events_data)
        logger.info(f"Found {len(events_data)} events")

        # Step 2: Extract Companies from Events
        task_status["message"] = "Extracting companies from events..."
        task_status["progress"] = 30
        all_companies = []
        for event in events_data:
            companies = company_scraper.extract_companies_from_event(event)
            all_companies.extend(companies)

        # Deduplicate companies by name (case-insensitive)
        unique_companies = {}
        for company in all_companies:
            name = company.get('name', '').strip().lower() if isinstance(company, dict) else getattr(company, 'name', '').strip().lower()
            if name and name not in unique_companies:
                unique_companies[name] = company

        # Enrich company contacts with LinkedIn
        for company in unique_companies.values():
            if not company.get('key_contacts'):
                contacts = enrich_contacts_with_linkedin(company.get('name', ''), company.get('website', ''))
                company['key_contacts'] = contacts

        companies_storage.extend(list(unique_companies.values()))
        logger.info(f"Found {len(unique_companies)} unique companies")

        # Step 3: Enrich Company Data
        task_status["message"] = "Enriching company data..."
        task_status["progress"] = 50
        enriched_companies = []
        unique_companies_list = list(unique_companies.values())[:max_leads]  # Limit processing
        for i, company in enumerate(unique_companies_list):
            enriched = company_scraper.enrich_company_data(company)
            enriched_companies.append(enriched)
            # Update progress
            progress = 50 + (i / min(len(unique_companies_list), max_leads)) * 20
            task_status["progress"] = int(progress)

        # Step 4: Qualify Leads
        task_status["message"] = "Qualifying leads with AI..."
        task_status["progress"] = 70
        qualified_leads = []
        for company in enriched_companies:
            # Find relevant event context
            relevant_events = [e for e in events_data if any(
                (comp.get('name', '').lower() if isinstance(comp, dict) else getattr(comp, 'name', '').lower()) == company.get('name', '').lower()
                for comp in getattr(e, 'companies', [])
            )]
            event_context = relevant_events[0] if relevant_events else None
            # Qualify the lead
            qualification = lead_qualifier.qualify_lead(company, event_context)
            if qualification.get('is_qualified', False):
                lead_data = {
                    "id": f"lead_{len(qualified_leads)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "company_name": company.get('name', ''),
                    "company_description": company.get('description', ''),
                    "company_size": company.get('size', ''),
                    "industry": company.get('industry', ''),
                    "revenue": company.get('revenue', ''),
                    "website": company.get('website', ''),
                    "qualification_score": qualification.get('score', 0),
                    "qualification_reasons": qualification.get('reasons', []),
                    "industry_alignment": qualification.get('industry_alignment', ''),
                    "event_context": event_context.get('name', '') if event_context else '',
                    "contact_name": company.get('key_contacts', [{}])[0].get('name', ''),
                    "contact_title": company.get('key_contacts', [{}])[0].get('title', ''),
                    "contact_linkedin": company.get('key_contacts', [{}])[0].get('linkedin', ''),
                    "created_at": datetime.now().isoformat()
                }
                qualified_leads.append(lead_data)
        leads_storage.extend(qualified_leads)
        logger.info(f"Qualified {len(qualified_leads)} leads")

        # Step 5: Generate Outreach (if requested)
        generated_outreach = []
        if include_outreach and qualified_leads:
            task_status["message"] = "Generating personalized outreach..."
            task_status["progress"] = 80
            outreach_results = outreach_generator.generate_bulk_outreach(qualified_leads)
            for result in outreach_results:
                if result.get('success', False):
                    outreach_data = {
                        "id": f"outreach_{result.get('lead_id', 'unknown')}",
                        "lead_id": result.get('lead_id'),
                        "subject_line": result['data']['subject_line'],
                        "primary_message": result['data']['primary_message'],
                        "follow_up_sequence": result['data']['follow_up_sequence'],
                        "personalization_elements": result['data']['personalization_elements'],
                        "generated_at": result['data']['generated_at'],
                        "status": "generated"
                    }
                    generated_outreach.append(outreach_data)
            outreach_storage.extend(generated_outreach)

        # Complete the task
        task_status = {
            "current_task": "lead_generation",
            "status": "completed",
            "progress": 100,
            "message": "Lead generation process completed successfully",
            "results": {
                "events_found": len(events_data),
                "companies_analyzed": len(unique_companies),
                "qualified_leads": len(qualified_leads),
                "outreach_generated": len(generated_outreach),
                "completion_time": datetime.now().isoformat()
            }
        }
        logger.info("Lead generation pipeline completed successfully")
    except Exception as e:
        logger.error(f"Error in lead generation pipeline: {str(e)}")
        task_status = {
            "current_task": "lead_generation",
            "status": "error",
            "progress": 0,
            "message": f"Error: {str(e)}",
            "results": {}
        }

@app.get("/api/task-status")
async def get_task_status():
    """Get current task status"""
    return task_status

@app.get("/api/dashboard")
async def get_dashboard_stats() -> DashboardStats:
    """Get dashboard statistics"""
    qualified_leads = [lead for lead in leads_storage if lead.get('qualification_score', 0) >= 0.8]
    avg_score = 0
    if leads_storage:
        total_score = sum(lead.get('qualification_score', 0) for lead in leads_storage)
        avg_score = total_score / len(leads_storage)
    return DashboardStats(
        total_leads=len(leads_storage),
        qualified_leads=len(qualified_leads),
        events_processed=len(events_storage),
        companies_analyzed=len(companies_storage),
        outreach_generated=len(outreach_storage),
        average_qualification_score=round(avg_score, 2)
    )

@app.get("/api/leads")
async def get_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    sort_by: str = Query("qualification_score", pattern="^(qualification_score|company_name|created_at)$")
):
    """Get paginated list of leads"""
    # Filter by minimum score
    filtered_leads = [
        lead for lead in leads_storage
        if lead.get('qualification_score', 0) >= min_score
    ]
    # Sort leads
    reverse = sort_by == "qualification_score" or sort_by == "created_at"
    sorted_leads = sorted(
        filtered_leads,
        key=lambda x: x.get(sort_by, 0),
        reverse=reverse
    )
    # Pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_leads = sorted_leads[start_idx:end_idx]
    # Add outreach information
    for lead in paginated_leads:
        lead_outreach = [
            outreach for outreach in outreach_storage
            if outreach.get('lead_id') == lead.get('id')
        ]
        lead['has_outreach'] = len(lead_outreach) > 0
        lead['outreach_data'] = lead_outreach[0] if lead_outreach else None
    return {
        "leads": paginated_leads,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(sorted_leads),
            "total_pages": (len(sorted_leads) + limit - 1) // limit
        },
        "filters": {
            "min_score": min_score,
            "sort_by": sort_by
        }
    }

@app.get("/api/leads/{lead_id}")
async def get_lead_detail(lead_id: str = Path(..., description="Lead ID")):
    """Get detailed information for a specific lead"""
    lead = next((lead for lead in leads_storage if lead.get('id') == lead_id), None)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    # Get associated outreach
    outreach_data = [
        outreach for outreach in outreach_storage
        if outreach.get('lead_id') == lead_id
    ]
    # Get related event information
    event_name = lead.get('event_context', '')
    related_event = next(
        (event for event in events_storage if event.name == event_name),
        None
    )
    return {
        "lead": lead,
        "outreach": outreach_data,
        "related_event": related_event
    }

@app.get("/api/events")
async def get_events():
    """Get list of scraped events"""
    return {
        "events": events_storage,
        "total": len(events_storage)
    }

@app.get("/api/companies")
async def get_companies(limit: int = Query(50, ge=1, le=200)):
    """Get list of scraped companies"""
    return {
        "companies": companies_storage[:limit],
        "total": len(companies_storage),
        "showing": min(limit, len(companies_storage))
    }

@app.post("/api/outreach/{lead_id}/generate")
async def generate_outreach_for_lead(lead_id: str = Path(..., description="Lead ID")):
    """Generate outreach message for a specific lead"""
    lead = next((lead for lead in leads_storage if lead.get('id') == lead_id), None)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    # Check if outreach already exists
    existing_outreach = next(
        (outreach for outreach in outreach_storage if outreach.get('lead_id') == lead_id),
        None
    )
    if existing_outreach:
        return {
            "message": "Outreach already exists for this lead",
            "outreach": existing_outreach
        }
    # Generate new outreach
    result = outreach_generator.generate_personalized_outreach(lead)
    if result.get('success', False):
        outreach_data = {
            "id": f"outreach_{lead_id}",
            "lead_id": lead_id,
            "subject_line": result['data']['subject_line'],
            "primary_message": result['data']['primary_message'],
            "follow_up_sequence": result['data']['follow_up_sequence'],
            "personalization_elements": result['data']['personalization_elements'],
            "generated_at": result['data']['generated_at'],
            "status": "generated"
        }
        outreach_storage.append(outreach_data)
        return {
            "message": "Outreach generated successfully",
            "outreach": outreach_data
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate outreach: {result.get('error', 'Unknown error')}"
        )

@app.delete("/api/leads/clear")
async def clear_all_data():
    """Clear all stored data (for testing purposes)"""
    global leads_storage, events_storage, companies_storage, outreach_storage, task_status
    leads_storage.clear()
    events_storage.clear()
    companies_storage.clear()
    outreach_storage.clear()
    task_status = {
        "current_task": None,
        "status": "idle",
        "progress": 0,
        "message": "",
        "results": {}
    }
    return {"message": "All data cleared successfully"}

@app.get("/api/export/leads")
async def export_leads():
    """Export leads data as JSON"""
    return {
        "export_type": "leads",
        "exported_at": datetime.now().isoformat(),
        "data": leads_storage,
        "count": len(leads_storage)
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if os.getenv("DEBUG") == "true" else None
        }
    )