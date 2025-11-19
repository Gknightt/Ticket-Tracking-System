# A.15 Licensing and Open Source Libraries

## Overview
This document provides a comprehensive overview of all open-source dependencies used in the Ticket Tracking System, ensuring legal compliance and transparency. The system uses numerous open-source libraries across backend (Python/Django), frontend (React/Node.js), and infrastructure components.

## Project License

### Main Repository License
**License**: MIT License (Recommended)

**Rationale**:
- Permissive license allowing commercial use
- Compatible with all dependencies
- Allows modification and distribution
- Minimal restrictions on usage

**License Text** (to be added to `LICENSE` file at repository root):
```
MIT License

Copyright (c) 2025 Ticket Tracking System Contributors

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

## Python Dependencies

### Core Framework
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| Django | 5.2.4 | BSD-3-Clause | Web framework |
| djangorestframework | 3.16.0 | BSD-3-Clause | REST API framework |
| djangorestframework_simplejwt | 5.5.0 | MIT | JWT authentication |
| drf-spectacular | 0.28.0 | BSD-3-Clause | API documentation |
| django-cors-headers | 4.7.0 | MIT | CORS handling |
| django-filter | 25.1 | BSD-3-Clause | Filtering support |

### Authentication & Security
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| argon2-cffi | 23.1.0+ | MIT | Password hashing |
| argon2-cffi-bindings | 21.2.0+ | MIT | Argon2 bindings |
| PyJWT | 2.9.0 | MIT | JWT token handling |
| cryptography | 45.0.4 | Apache-2.0/BSD | Cryptographic operations |
| djangorestframework-api-key | Latest | MIT | API key authentication |
| django-simple-captcha | 0.6.0 | MIT | CAPTCHA support |

### Database & ORM
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| psycopg2-binary | 2.9+ | LGPL-3.0 | PostgreSQL adapter |
| dj-database-url | 2.1.0 | BSD | Database URL parsing |
| django-extensions | 4.1 | MIT | Django extensions |

### Task Queue & Messaging
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| celery | 5.5.3 | BSD-3-Clause | Distributed task queue |
| django-celery-results | 2.5.1 | BSD | Celery result backend |
| amqp | 5.3.1 | BSD | AMQP protocol |
| kombu | 5.5.4 | BSD | Messaging library |
| billiard | 4.2.1 | BSD | Process pooling |
| vine | 5.1.0 | BSD | Promises/futures |

### WebSockets & Real-time
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| channels | Latest | BSD-3-Clause | WebSocket support |
| daphne | Latest | BSD-3-Clause | ASGI server |

### File Processing
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| Pillow | 11.2.1 | HPND | Image processing |
| pdfplumber | 0.11.7 | MIT | PDF parsing |
| pdfminer.six | 20250506 | MIT | PDF text extraction |
| pypdfium2 | 4.30.1 | Apache-2.0/BSD | PDF rendering |
| python-docx | 1.2.0 | MIT | Word document processing |
| lxml | 5.4.0 | BSD | XML/HTML processing |

### Utilities
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| requests | 2.32.4 | Apache-2.0 | HTTP client |
| python-decouple | 3.8 | MIT | Settings management |
| python-dotenv | 1.1.0 | BSD-3-Clause | .env file support |
| Faker | 37.4.0 | MIT | Test data generation |
| PyYAML | 6.0.2 | MIT | YAML parsing |

### Web Server & Deployment
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| gunicorn | 21.2.0 | MIT | WSGI HTTP server |
| whitenoise | 6.6.0 | MIT | Static file serving |

### Supporting Libraries
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| asgiref | 3.9.1 | BSD-3-Clause | ASGI utilities |
| attrs | 25.3.0 | MIT | Python classes |
| certifi | 2025.6.15 | MPL-2.0 | SSL certificates |
| cffi | 1.17.1 | MIT | C bindings |
| charset-normalizer | 3.4.2 | MIT | Character encoding |
| click | 8.2.1 | BSD-3-Clause | CLI creation |
| click-didyoumean | 0.3.1 | MIT | CLI suggestions |
| click-plugins | 1.1.1 | BSD-3-Clause | Click plugins |
| click-repl | 0.3.0 | MIT | REPL for Click |
| colorama | 0.4.6 | BSD-3-Clause | Terminal colors |
| idna | 3.10 | BSD-3-Clause | Internationalized domains |
| inflection | 0.5.1 | MIT | String transformations |
| jsonschema | 4.24.0 | MIT | JSON schema validation |
| jsonschema-specifications | 2025.4.1 | MIT | JSON schema specs |
| packaging | 25.0 | Apache-2.0/BSD | Version handling |
| prompt_toolkit | 3.0.51 | BSD-3-Clause | Interactive prompts |
| pycparser | 2.22 | BSD-3-Clause | C parser |
| python-dateutil | 2.9.0.post0 | Apache-2.0/BSD | Date utilities |
| referencing | 0.36.2 | MIT | JSON reference resolution |
| rpds-py | 0.25.1 | MIT | Persistent data structures |
| setuptools | 80.9.0 | MIT | Package management |
| six | 1.17.0 | MIT | Python 2/3 compatibility |
| sqlparse | 0.5.3 | BSD-3-Clause | SQL parsing |
| typing_extensions | 4.14.0 | PSF | Type hints |
| tzdata | 2025.2 | Apache-2.0 | Timezone data |
| uritemplate | 4.2.0 | Apache-2.0/BSD | URI templates |
| urllib3 | 2.5.0 | MIT | HTTP client |
| wcwidth | 0.2.13 | MIT | Terminal width |

## Frontend Dependencies (React/Node.js)

### Core Framework
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| react | ^18.2.0 | MIT | UI library |
| react-dom | ^18.2.0 | MIT | React DOM rendering |
| react-router-dom | ^7.6.2 | MIT | Routing |
| vite | ^7.1.3 | MIT | Build tool |

### UI Components & Visualization
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| chart.js | ^4.5.0 | MIT | Charting library |
| react-chartjs-2 | ^5.3.0 | MIT | React wrapper for Chart.js |
| reactflow | ^11.11.4 | MIT | Node-based UI |
| @reactflow/core | ^11.11.4 | MIT | ReactFlow core |
| lucide-react | ^0.523.0 | ISC | Icon library |
| react-icons | ^5.5.0 | MIT | Icon library |
| @fortawesome/fontawesome-free | ^6.7.2 | CC-BY-4.0/MIT | Font Awesome icons |
| font-awesome | ^4.7.0 | OFL-1.1/MIT | Font Awesome (legacy) |
| react-step-progress-bar | ^1.0.3 | MIT | Progress indicators |

### Form & Input Components
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| react-datepicker | ^8.7.0 | MIT | Date picker component |
| date-fns | ^4.1.0 | MIT | Date utilities |
| dayjs | ^1.11.18 | MIT | Date manipulation |

### File & Document Processing
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| @react-pdf-viewer/core | ^3.12.0 | Apache-2.0 | PDF viewing |
| mammoth | ^1.9.1 | BSD-2-Clause | DOCX to HTML conversion |

### Utilities
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| axios | ^1.11.0 | MIT | HTTP client |
| dompurify | ^3.3.0 | Apache-2.0/MPL-2.0 | HTML sanitization |
| dagre | ^0.8.5 | MIT | Graph layout |
| uuid | ^11.1.0 | MIT | UUID generation |

### Build & Development Tools
| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| @vitejs/plugin-react | ^4.4.1 | MIT | Vite React plugin |
| eslint | ^9.25.0 | MIT | Linting |
| @eslint/js | ^9.25.0 | MIT | ESLint config |
| eslint-plugin-react-hooks | ^5.2.0 | MIT | React hooks linting |
| eslint-plugin-react-refresh | ^0.4.19 | MIT | React refresh linting |
| globals | ^16.0.0 | MIT | Global variables |
| esbuild | ^0.25.9 | MIT | JavaScript bundler |
| @types/react | ^19.1.2 | MIT | React TypeScript types |
| @types/react-dom | ^19.1.2 | MIT | React DOM TypeScript types |

## Infrastructure Dependencies

### Containerization
| Software | Version | License | Purpose |
|----------|---------|---------|---------|
| Docker | 20+ | Apache-2.0 | Containerization |
| Docker Compose | 2.0+ | Apache-2.0 | Multi-container orchestration |

### Database
| Software | Version | License | Purpose |
|----------|---------|---------|---------|
| PostgreSQL | 15 | PostgreSQL License | Relational database |

### Message Queue
| Software | Version | License | Purpose |
|----------|---------|---------|---------|
| RabbitMQ | 3-management | MPL-2.0 | Message broker |

### Base Images
| Image | License | Purpose |
|-------|---------|---------|
| python:3.11-slim | PSF | Python runtime |
| postgres:15 | PostgreSQL License | Database |
| rabbitmq:3-management | MPL-2.0 | Message queue |
| node:18-alpine | MIT | Node.js runtime (frontend) |

## License Compatibility Matrix

### Compatible Licenses
The project uses MIT license, which is compatible with:
- ✅ MIT License
- ✅ BSD License (2-Clause, 3-Clause)
- ✅ Apache License 2.0
- ✅ ISC License
- ✅ PSF License
- ✅ MPL-2.0 (Mozilla Public License)

### Licenses Requiring Attribution
The following licenses require attribution in distributed software:
- **BSD Licenses**: Include copyright notice
- **Apache 2.0**: Include NOTICE file if present
- **CC-BY-4.0**: Provide attribution

### LGPL Dependencies
| Package | License | Compliance |
|---------|---------|------------|
| psycopg2-binary | LGPL-3.0 | ✅ Dynamic linking allowed |

**Compliance Note**: LGPL allows dynamic linking without licensing the entire application under LGPL. PostgreSQL driver is used as a library, not modified, which satisfies LGPL requirements.

## License Compliance Procedures

### Automated License Checking

#### Python Dependencies
```bash
# Install license checker
pip install pip-licenses

# Generate license report
pip-licenses --format=markdown --with-urls --output-file=licenses-python.md

# Check for GPL licenses (may require special handling)
pip-licenses | grep GPL
```

#### Node.js Dependencies
```bash
# Install license checker
npm install -g license-checker

# Generate license report
npx license-checker --json --out licenses-frontend.json

# Check for problematic licenses
npx license-checker --failOn "GPL;AGPL"
```

### Manual Review Process
1. **New Dependency Addition**:
   - Check license compatibility
   - Add to this documentation
   - Verify no GPL/AGPL conflicts (unless intentional)

2. **Quarterly Review**:
   - Run automated license checks
   - Review new dependencies
   - Update documentation
   - Verify compliance

3. **Pre-Release Checklist**:
   - ✅ All dependencies documented
   - ✅ License compatibility verified
   - ✅ Attribution requirements met
   - ✅ NOTICE file updated (if needed)

## Attribution Requirements

### Required Attributions
The following components require attribution:

#### Font Awesome
- **License**: CC-BY-4.0 (fonts), MIT (code)
- **Attribution**: "Font Awesome by Fonticons, Inc."
- **Link**: https://fontawesome.com

#### Other MIT/BSD Libraries
Standard copyright notices included in dependency files satisfy attribution requirements.

## Vulnerability Management

### Automated Scanning
- **GitHub Dependabot**: Monitors for known vulnerabilities
- **npm audit**: Frontend dependency vulnerabilities
- **pip-audit**: Python dependency vulnerabilities (planned)

### Update Policy
- **Security vulnerabilities**: Patched within 48 hours
- **Regular updates**: Monthly dependency review
- **Major version updates**: Evaluated quarterly

## License Report Generation

### For Distribution/Deployment
When distributing the software, include:

1. **LICENSE file**: Project's MIT license
2. **NOTICE file**: Third-party attributions
3. **licenses/ directory**: Complete license texts for all dependencies

### Automated Generation Script
```bash
#!/bin/bash
# Generate comprehensive license report

echo "Generating Python dependency licenses..."
pip-licenses --format=markdown --with-urls > docs/licenses-python.md

echo "Generating Frontend dependency licenses..."
cd frontend
npx license-checker --json --out ../docs/licenses-frontend.json

echo "License report generated successfully!"
```

## Legal Disclaimer

THE SOFTWARE AND ALL DEPENDENCIES ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. This document represents a good-faith effort to comply with all open-source licenses. Users are responsible for verifying license compliance for their specific use case.

For legal questions, consult with a qualified attorney specializing in open-source licensing.

## Contact

For licensing questions or concerns:
- **Repository**: https://github.com/Gknightt/Ticket-Tracking-System
- **Issues**: https://github.com/Gknightt/Ticket-Tracking-System/issues
- **Email**: [Project maintainer email]

## References

- [Choose a License](https://choosealicense.com/)
- [Open Source Initiative](https://opensource.org/licenses)
- [SPDX License List](https://spdx.org/licenses/)
- [GNU License Compatibility](https://www.gnu.org/licenses/license-list.html)
- [Django License](https://github.com/django/django/blob/main/LICENSE)
- [React License](https://github.com/facebook/react/blob/main/LICENSE)

---

**Last Updated**: November 2025
**Review Frequency**: Quarterly
**Next Review**: February 2026
