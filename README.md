🔍 **Real-time compliance checks, company profile lookups, and risk scoring for Dutch companies (KVK) with international sanctions screening.**

[![CI](https://github.com/TCLUBNL/compliance_copilot_mcp_server/actions/workflows/ci.yml/badge.svg)](https://github.com/TCLUBNL/compliance_copilot_mcp_server/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Start

### Installation

Clone and install:
- Clone the repository
- Create virtual environment
- Install dependencies from requirements.txt

### Running the API Server

Start the development server with python run.py

The API will be available at http://localhost:8000

## 📚 API Documentation

Interactive documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 🎯 Features

- 🏢 Company Search - Search Dutch Chamber of Commerce (KVK) database
- 📊 Company Profiles - Detailed company information retrieval
- ⚠️ Risk Scoring - Automated compliance risk assessment
- 🌍 Sanctions Screening - Check against OpenSanctions database
- 🔒 Secure & Fast - Redis caching, rate limiting, and authentication ready

## 🔌 API Endpoints

Health Check: GET /health
Search Companies: GET /api/v1/search?query=Tesla
Get Company Profile: GET /api/v1/profile/12345678
Risk Assessment: GET /api/v1/risk/12345678
Sanctions Screening: GET /api/v1/sanctions/screen?name=Tesla

## 🧪 Development

Run tests: pytest --cov=services
Format code: black . && ruff check . --fix
Pre-commit hooks: pre-commit install

## 📝 License

MIT License

## 🆘 Support

- Email: support@tclubnl.com
- Issues: https://github.com/TCLUBNL/compliance_copilot_mcp_server/issues
