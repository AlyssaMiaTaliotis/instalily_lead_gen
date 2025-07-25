# Instalily AI - Lead Generation System

Automated lead generation and outreach system for DuPont Tedlar Graphics & Signage division.

---

## Overview

Instalily AI is an intelligent lead generation platform that automatically discovers industry events, identifies potential customers, qualifies leads using AI, and generates personalized outreach messages. Built for the graphics and signage industry to help sales teams efficiently engage with high-quality prospects.

---

## Features

- **Automated Event Discovery**
  - Scrapes major industry events (ISA Sign Expo, PRINTING United, etc.)
  - Extracts exhibitor lists and company information
  - Tracks event dates, locations, and industry focus

- **Intelligent Company Research**
  - Discovers companies from event exhibitor lists
  - Enriches company data with website scraping
  - Gathers company size, revenue, technology stack
  - Identifies key decision makers

- **AI-Powered Lead Qualification**
  - Uses machine learning to score lead quality
  - Analyzes industry alignment and company fit
  - Prioritizes leads based on revenue potential
  - Considers technology compatibility

- **Personalized Outreach Generation**
  - Creates custom email sequences for each lead
  - Incorporates event context and company insights
  - Generates follow-up messages
  - Maintains professional tone and messaging

- **Interactive Dashboard**
  - Real-time lead generation progress
  - Filterable lead lists with qualification scores
  - Event tracking and company analytics
  - Export capabilities for CRM integration

---

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key (for AI features)

### Installation

**Clone the repository**
```sh
git clone https://github.com/AlyssaMiaTaliotis/instalily_lead_gen.git
cd instalily_lead_gen
```

## Backend Setup

```
cd backend
pip install -r requirements.txt
```

# Set environment variables

```
export OPENAI_API_KEY="your-openai-api-key"
```
## Frontend Setup

```
cd frontend/dashboard
npm install
```

## Running the Application

### Start the Backend

```
cd backend
uvicorn main:app --reload --port 8000
```

### Start the Frontend

```
cd frontend/dashboard
npm start
```

Access the Dashboard: http://localhost:3000
API Base URL: http://localhost:8000

Change API_BASE in frontend/dashboard/src/App.js to  http://localhost:8000 to run locally. 


---

## Configuration

### Environment Variables

```
OPENAI_API_KEY=your-openai-api-key-here
```

### Target Industries 

Configure in ```backend/scrapers/company_scraper.py```:

```
target_industries = [
    "graphics",
    "signage", 
    "printing",
    "advertising",
    "specialty materials"
]
```

---

## Usage Guide

### 1. Generate Leads
- Navigate to the dashboard
- Click "Start Lead Generation"
- Configure your search parameters:
  - Target industries
  - Maximum leads
  - Minimum company size
  - Include outreach generation
- Monitor progress in real-time

### 2. Review & Qualify Leads
- Access the leads table
- Filter by qualification score
- Review company details and event context
- Export qualified leads for CRM import

### 3. Outreach Management
- View generated outreach messages
- Customize messages as needed
- Copy to your email client or CRM
- Track engagement metrics

---

## Performance & Scalability

### Current Limitations
- **Rate Limiting:** Web scraping is throttled to avoid blocking
- **API Limits:** OpenAI API calls are rate-limited
- **Concurrent Users:** Single-instance deployment

---

## Security & Compliance

- No personal data stored permanently
- API keys encrypted in environment
- Rate limiting on all endpoints
- Input validation and sanitization

### Web Scraping Ethics
- Respects robots.txt files
- Implements request delays
- Uses appropriate User-Agent headers
- Monitors for IP blocking

### GDPR Compliance
- Minimal data collection
- Clear data retention policies
- User consent mechanisms
- Data export capabilities

---

## Roadmap

**Phase 1: Core Features**
- [x] Event scraping
- [x] Company discovery
- [x] Lead qualification
- [x] Basic dashboard

**Phase 2: AI Enhancement**
- [ ] Advanced ML models for scoring
- [ ] Sentiment analysis of company news
- [ ] Predictive lead timing
- [ ] A/B testing for outreach

**Phase 3: Enterprise Features**
- [ ] CRM integrations (Salesforce, HubSpot)
- [ ] Email automation workflows
- [ ] Advanced analytics and reporting
- [ ] Multi-tenant architecture
- [ ] Mobile application

**Phase 4: Scale & Optimize**
- [ ] Real-time event monitoring
- [ ] Social media integration
- [ ] International market expansion
- [ ] Advanced personalization engine

---

## Common Issues

- ChromeDriver not found

```
brew install chromedriver         # macOS
```

- OpenAI API rate limit exceeded

Check your API usage at platform.openai.com

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
