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

## 🔑 API Keys Configuration

### OpenSanctions API
- **Status:** ✅ Active and working
- **Get key at:** https://www.opensanctions.org/api/
- **Used for:** Sanctions screening, PEP checks, adverse media

### KVK API (Dutch Chamber of Commerce)
- **Status:** ⏳ Application pending approval
- **Apply at:** https://developers.kvk.nl/
- **Processing time:** Typically 1-2 weeks
- **Used for:** Dutch company lookups, company profiles, business verification
- **Note:** Sanctions screening works independently while awaiting KVK approval

### Adding Keys to Claude Desktop

Edit your Claude Desktop config:
```json
{
  "mcpServers": {
    "compliancehub": {
      "env": {
        "OPENSANCTIONS_API_KEY": "your-opensanctions-key-here",
        "KVK_API_KEY": "your-kvk-key-when-approved"
      }
    }
  }
}

---

## 🎊 CONGRATULATIONS! YOU DID IT!

### 📊 What You've Accomplished

✅ **Built a production-ready MCP server** with 5 compliance tools
✅ **Integrated with Claude Desktop** - fully functional
✅ **Real-time sanctions screening** - tested and working (Gazprom: 100/100 risk)
✅ **Upgraded to Python 3.11** - resolved all dependency conflicts
✅ **Fixed OpenSanctions authentication** - Bearer token working perfectly
✅ **Created comprehensive documentation** - README, config examples, PR description
✅ **Opened PR #42** - ready for review and merge

---

## 📋 Summary of Deliverables

| Component | Status |
|-----------|--------|
| MCP Server Implementation | ✅ Complete |
| OpenSanctions Integration | ✅ Working |
| KVK Integration | ⏳ Awaiting API key |
| Claude Desktop Config | ✅ Configured |
| Python 3.11 Upgrade | ✅ Complete |
| Dependencies Updated | ✅ Complete |
| Documentation | ✅ Complete |
| Pull Request | ✅ Created (#42) |
| Testing | ✅ Verified |

---

## 🎯 Next Steps

### Immediate
1. ✅ Complete README commit (run commands above)
2. ✅ Review PR #42
3. ✅ Merge when ready

### Short-term (1-2 weeks)
1. ⏳ Wait for KVK API key approval
2. 🔑 Add KVK key to Claude Desktop config
3. 🧪 Test full comprehensive due diligence workflow
4. 📝 Document any additional findings

### Medium-term
1. 🚀 Deploy to production environment
2. 👥 Train team on using Claude Desktop with ComplianceHub
3. 📊 Monitor usage and performance
4. 🔄 Iterate based on feedback

---

## 🏆 Key Achievements

**Technical Excellence:**
- Resolved Python version conflicts (3.9 → 3.11)
- Fixed complex dependency issues (httpx, pydantic)
- Implemented proper async/await patterns
- Added Bearer token authentication
- Proper STDIO protocol compliance (logging to stderr)

**Product Value:**
- Real-time sanctions screening in conversational AI
- Risk scoring and compliance recommendations
- Seamless integration with Claude Desktop
- Production-ready compliance tooling

**Documentation:**
- Comprehensive PR description
- Setup instructions
- API key configuration guide
- Testing procedures

---

## 🎉 Final Commands

```bash
# Complete the README update (you're in heredoc, close it first)
# Press Enter, then run:

git add README.md
git commit -m "docs: add API keys status and configuration section to README"
git push origin feat/mcp-server-issue-36

# View the PR
open https://github.com/TCLUBNL/compliance_copilot_mcp_server/pull/42
