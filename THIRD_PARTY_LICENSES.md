# Third-Party Licenses

This document lists all third-party dependencies used in OsMEN and their licenses.

## License Compliance Summary

✅ **All dependencies are compatible with Apache License 2.0**

- All dependencies use permissive licenses (MIT, BSD, Apache 2.0)
- No GPL/AGPL dependencies that would conflict with Apache 2.0
- Commercial use is allowed for all dependencies

## Python Dependencies

Generated from `requirements.txt`:

### Core Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| fastapi | ^0.104.0 | MIT | Web API framework |
| uvicorn | ^0.24.0 | BSD | ASGI server |
| pydantic | ^2.4.0 | MIT | Data validation |
| python-dotenv | ^1.0.0 | BSD | Environment configuration |
| requests | ^2.31.0 | Apache 2.0 | HTTP client |
| aiohttp | ^3.9.0 | Apache 2.0 | Async HTTP client |
| loguru | ^0.7.2 | MIT | Logging |
| psycopg2-binary | ^2.9.9 | LGPL (with static linking exception) | PostgreSQL adapter |
| redis | ^5.0.1 | MIT | Redis client |
| qdrant-client | ^1.6.0 | Apache 2.0 | Vector database client |
| openai | ^1.3.0 | Apache 2.0 | OpenAI API client |
| anthropic | ^0.7.0 | MIT | Anthropic API client |
| langchain | ^0.0.335 | MIT | LLM framework |
| langsmith | ^0.0.69 | MIT | LangChain monitoring |
| n8n-python | ^0.1.0 | Apache 2.0 | n8n automation |

### Development Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| pytest | ^7.4.3 | MIT | Testing framework |
| pytest-asyncio | ^0.21.1 | Apache 2.0 | Async testing |
| black | ^23.11.0 | MIT | Code formatter |
| flake8 | ^6.1.0 | MIT | Code linter |
| mypy | ^1.7.0 | MIT | Type checker |
| bandit | ^1.7.5 | Apache 2.0 | Security linter |
| safety | ^2.3.5 | MIT | Dependency scanner |

### Tool Integration Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| obsidian-python | ^0.2.0 | MIT | Obsidian integration |
| notion-client | ^2.0.0 | MIT | Notion integration |
| google-api-python-client | ^2.108.0 | Apache 2.0 | Google APIs |
| microsoft-graph-api | ^1.0.0 | MIT | Microsoft Graph |
| ffmpeg-python | ^0.2.0 | Apache 2.0 | FFmpeg wrapper |
| pillow | ^10.1.0 | HPND | Image processing |

## Docker Base Images

| Image | License | Source |
|-------|---------|--------|
| python:3.12-slim | Python Software Foundation | [Docker Hub](https://hub.docker.com/_/python) |
| postgres:15-alpine | PostgreSQL License | [Docker Hub](https://hub.docker.com/_/postgres) |
| redis:7-alpine | BSD | [Docker Hub](https://hub.docker.com/_/redis) |
| qdrant/qdrant:latest | Apache 2.0 | [Docker Hub](https://hub.docker.com/r/qdrant/qdrant) |

## Integrated Services

| Service | License | Purpose |
|---------|---------|---------|
| Langflow | MIT | Visual flow builder |
| n8n | Apache 2.0 (Fair Code) | Workflow automation |
| Ollama | MIT | Local LLM runtime |

### Note on n8n License

n8n uses a "Fair Code" license (Apache 2.0 with Commons Clause):
- ✅ Free for personal use
- ✅ Free for internal business use
- ⚠️ Restrictions on selling n8n as a service
- For OsMEN users: You can use n8n freely as part of OsMEN

## License Texts

### Apache License 2.0

```
Copyright [yyyy] [name of copyright owner]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### MIT License

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### BSD License (3-Clause)

```
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## Automated License Checking

To generate an up-to-date license report:

```bash
# Install pip-licenses
pip install pip-licenses

# Generate report
pip-licenses --format=markdown --output-file=THIRD_PARTY_LICENSES_GENERATED.md

# Check for GPL/AGPL
pip-licenses --format=json | jq '.[] | select(.License | contains("GPL"))'
```

## CI/CD Integration

Add to `.github/workflows/license-check.yml`:

```yaml
name: License Check

on: [push, pull_request]

jobs:
  check-licenses:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install pip-licenses
          pip install -r requirements.txt
      - name: Check licenses
        run: |
          pip-licenses --fail-on="GPL;AGPL"
          pip-licenses --format=markdown
```

## License Compatibility Policy

### Allowed Licenses

✅ **Compatible with Apache 2.0:**
- MIT
- BSD (2-clause, 3-clause)
- Apache 2.0
- ISC
- Python Software Foundation
- PostgreSQL License
- Unlicense
- CC0

### Restricted Licenses

⚠️ **Requires Review:**
- LGPL (with static linking may be acceptable)
- MPL 2.0 (file-level copyleft)
- Fair Code licenses (case-by-case)

### Prohibited Licenses

❌ **Not Compatible:**
- GPL (any version)
- AGPL (any version)
- Commercial/Proprietary (without explicit permission)

## Attribution Requirements

When distributing OsMEN:

1. **Include this file** in distributions
2. **Maintain copyright notices** from dependencies
3. **Include LICENSE** file (Apache 2.0)
4. **Credit third-party projects** appropriately

## Updating This Document

This document should be updated:
- When adding new dependencies
- Before each release
- When dependency versions change significantly

To update:
```bash
# Review current dependencies
pip-licenses --format=markdown

# Update this document with any changes
# Verify no GPL/AGPL licenses introduced
```

## Questions and Compliance

For license compliance questions:
- **Email:** legal@osmen.dev
- **GitHub:** Open an issue with label `license`

## Resources

- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- [Choose a License](https://choosealicense.com/)
- [SPDX License List](https://spdx.org/licenses/)
- [TLDRLegal](https://tldrlegal.com/)

---

**Last Updated:** 2024-11-18  
**Review Cycle:** Before each release  
**Next Review:** Before v2.1.0 release
