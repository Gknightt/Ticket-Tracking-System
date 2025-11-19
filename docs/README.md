# Ticket Tracking System - Comprehensive Documentation

This directory contains the complete technical documentation for the Ticket Tracking System, a distributed microservices-based ticketing and workflow management platform.

---

## Documentation Index

### [A.1 System Architecture](./A1_SYSTEM_ARCHITECTURE.md)
**Technical blueprint of the entire system**

Covers:
- Executive summary and architectural principles  
- High-level architecture diagrams  
- Microservices architecture (auth, workflow_api, messaging, notification, ticket_service)  
- Component architecture with detailed service descriptions  
- Communication protocols (REST, AMQP/RabbitMQ, WebSocket)  
- Complete technology stack (Django 5.2.1, React 18, PostgreSQL 15, RabbitMQ)  
- Deployment architecture (Docker Compose + Cloud/Production)  
- Scalability, performance, and security architecture  
- Disaster recovery and high availability strategies

**Key Highlights**:
- Uses RabbitMQ directly as message broker (NOT Celery broker, but Celery workers consume from RabbitMQ)
- 5 main services with specific responsibilities
- Shared PostgreSQL with logical database separation
- JWT-based authentication across all services

---

### [A.2 Information Systems Integration](./A2_INFORMATION_SYSTEMS_INTEGRATION.md)
**How different software systems are connected as one unified system**

Covers:
- Integration architecture and patterns
- Integration points between all services
- Data flow diagrams (DFD Level 0, 1, 2)
- Inter-service communication matrix
- External system integration (HDTS, AMS, BMS)
- Data transformation and mapping examples
- Integration patterns (Request-Reply, Pub-Sub, Message Queue, Circuit Breaker)
- Error handling, retry strategies, and resilience
- Integration security and monitoring

**Key Highlights**:
- HDTS (Help Desk) sends tickets via Celery/RabbitMQ queue to workflow_api
- Workflow API triggers notifications via message queue
- WebSocket real-time updates for comments
- External AMS/BMS integration for asset and budget approval

---

### [A.3 Application Design and Development](./A3_APPLICATION_DESIGN_DEVELOPMENT.md)
**Low-level design and implementation details**

Covers:
- Software design patterns used (Repository, Service Layer, Serializer, Factory, Observer, Strategy, Chain of Responsibility)
- Backend architecture (Django layered structure)
- Key algorithms:
  - Round-robin task assignment
  - SLA calculation
  - Workflow matching
  - State machine for task transitions
- Code structure and organization
- Critical code implementations (ticket processing, WebSocket, JWT auth)
- Libraries and frameworks (complete version list)
- Development workflow and testing strategy

**Key Highlights**:
- Django REST Framework for API development
- Celery @shared_task pattern for background jobs
- React hooks for frontend state management
- Comprehensive testing strategy (unit, integration, E2E)

---

### [A.5 Network Configuration](./A5_NETWORK_CONFIGURATION.md)
**Network design, connectivity, and security**

Covers:
- Network topology (development and production)
- IP address schemes and port allocations
- Communication protocols (HTTP/HTTPS, WebSocket, AMQP, PostgreSQL)
- Firewall rules for public, private, and database subnets
- Security configuration (SSL/TLS, network segmentation, DDoS protection)
- Network monitoring and health checks
- Troubleshooting common network issues

**Key Highlights**:
- Development uses Docker bridge networking
- Production uses VPC with multiple subnets
- All external traffic goes through load balancer
- Database and RabbitMQ isolated in private subnet

---

### [A.10 APIs and Integration Points](./A10_APIS_INTEGRATION_POINTS.md)
**API documentation and integration guide**

Covers:
- Complete API reference for all services
- Authentication (JWT token flow)
- Auth Service APIs (user management, roles)
- Workflow API (workflows, tasks, audit logs)
- Messaging Service APIs (comments, WebSocket)
- Notification Service APIs (email, in-app notifications)
- API standards and conventions
- Error handling and rate limiting
- API testing examples (cURL, Postman, Python)

**Key Highlights**:
- RESTful APIs following OpenAPI 3.0
- JWT authentication with 15-minute access tokens
- WebSocket support for real-time updates
- Comprehensive error codes and responses

---

## Quick Navigation by Topic

### Architecture & Design
- [System Overview](./A1_SYSTEM_ARCHITECTURE.md#system-overview)
- [Microservices Architecture](./A1_SYSTEM_ARCHITECTURE.md#architecture-style)
- [Design Patterns](./A3_APPLICATION_DESIGN_DEVELOPMENT.md#software-design-patterns)
- [Backend Architecture](./A3_APPLICATION_DESIGN_DEVELOPMENT.md#backend-architecture)

### Integration
- [Integration Architecture](./A2_INFORMATION_SYSTEMS_INTEGRATION.md#integration-architecture)
- [Data Flow Diagrams](./A2_INFORMATION_SYSTEMS_INTEGRATION.md#data-flow-diagrams)
- [External Systems](./A2_INFORMATION_SYSTEMS_INTEGRATION.md#external-system-integration)
- [Message Queue Integration](./A2_INFORMATION_SYSTEMS_INTEGRATION.md#asynchronous-communication-message-queue)

### APIs & Development
- [API Overview](./A10_APIS_INTEGRATION_POINTS.md#api-overview)
- [Authentication](./A10_APIS_INTEGRATION_POINTS.md#authentication)
- [All API Endpoints](./A10_APIS_INTEGRATION_POINTS.md)
- [Development Workflow](./A3_APPLICATION_DESIGN_DEVELOPMENT.md#development-workflow)

### Network & Security
- [Network Topology](./A5_NETWORK_CONFIGURATION.md#network-topology)
- [Firewall Rules](./A5_NETWORK_CONFIGURATION.md#firewall-rules)
- [Security Configuration](./A5_NETWORK_CONFIGURATION.md#security-configuration)
- [Security Architecture](./A1_SYSTEM_ARCHITECTURE.md#security-architecture)

---

## Key System Characteristics

### Technology Stack
- **Backend**: Django 5.2.1, Django REST Framework 3.16.0
- **Frontend**: React 18, Vite
- **Message Broker**: RabbitMQ 3 (AMQP protocol)
- **Database**: PostgreSQL 15
- **Task Queue**: Celery 5.5.3 (workers only, not broker)
- **WebSocket**: Django Channels
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Containerization**: Docker + Docker Compose

### Main Services
1. **Auth Service** (Port 8003): Authentication, user management, RBAC
2. **Workflow API** (Port 8002): Workflow engine, task orchestration
3. **Messaging Service** (Port 8005): Real-time comments via WebSocket
4. **Notification Service** (Port 8006): Email and in-app notifications
5. **Ticket Service** (Port 8004): Mock HDTS integration for testing

### Communication Patterns
- **Synchronous**: REST APIs (service-to-service, frontend-to-backend)
- **Asynchronous**: RabbitMQ message queues (ticket ingestion, notifications)
- **Real-time**: WebSocket (comments, live updates)

---

## Important Notes

### RabbitMQ vs Celery
**Clarification**: The system uses RabbitMQ as the message broker. Celery is used ONLY as worker processes that consume tasks from RabbitMQ queues, NOT as a separate broker. This is an important distinction.

**Flow**:
```
Service → app.send_task() → RabbitMQ Queue → Celery Worker consumes → Executes task
```

### Ticket Service (Mock)
The `ticket_service` is a **mock service** that simulates the external HDTS (Help Desk & Ticketing System). In production, actual HDTS would send tickets directly to the `TICKET_TASKS_PRODUCTION` queue in RabbitMQ, and the workflow-worker would consume and process them.

---

## Getting Started

### For Developers
1. Read [A.3 Application Design and Development](./A3_APPLICATION_DESIGN_DEVELOPMENT.md#development-workflow)
2. Review [A.10 APIs and Integration Points](./A10_APIS_INTEGRATION_POINTS.md) for API usage
3. Study [Design Patterns](./A3_APPLICATION_DESIGN_DEVELOPMENT.md#software-design-patterns)

### For System Administrators
1. Read [A.1 System Architecture](./A1_SYSTEM_ARCHITECTURE.md#deployment-architecture)
2. Review [A.5 Network Configuration](./A5_NETWORK_CONFIGURATION.md)
3. Check [Security Configuration](./A5_NETWORK_CONFIGURATION.md#security-configuration)

### For Integration Engineers
1. Read [A.2 Information Systems Integration](./A2_INFORMATION_SYSTEMS_INTEGRATION.md)
2. Review [External System Integration](./A2_INFORMATION_SYSTEMS_INTEGRATION.md#external-system-integration)
3. Study [Integration Patterns](./A2_INFORMATION_SYSTEMS_INTEGRATION.md#integration-patterns)

### For API Consumers
1. Read [A.10 APIs and Integration Points](./A10_APIS_INTEGRATION_POINTS.md)
2. Check [Authentication](./A10_APIS_INTEGRATION_POINTS.md#authentication)
3. Review specific API sections for your use case

---

## Documentation Standards

All documentation follows these standards:
- **Format**: Markdown with table of contents
- **Code Examples**: Syntax-highlighted with language specification
- **Diagrams**: ASCII art for compatibility
- **Versioning**: Semantic versioning (v1.0)
- **Updates**: Dated and attributed to maintainer team

---

## Contributing to Documentation

When updating documentation:
1. Maintain consistent formatting and style
2. Update the last updated date
3. Add examples where applicable
4. Keep diagrams up to date
5. Update the README index if adding new sections

---

## Contact & Support

For questions or clarifications:
- **Architecture**: System Architecture Team
- **Integration**: Integration Architecture Team
- **Development**: Development Team
- **Network/Security**: Network Infrastructure Team
- **APIs**: API Development Team

---

## Document Versions

| Document | Version | Last Updated | Pages/Lines |
|----------|---------|--------------|-------------|
| A.1 System Architecture | 1.0 | 2025-11-19 | 850+ lines |
| A.2 Information Systems Integration | 1.0 | 2025-11-19 | 1150+ lines |
| A.3 Application Design and Development | 1.0 | 2025-11-19 | 650+ lines |
| A.5 Network Configuration | 1.0 | 2025-11-19 | 600+ lines |
| A.10 APIs and Integration Points | 1.0 | 2025-11-19 | 970+ lines |
| **Total** | - | - | **4200+ lines** |

---

## License

Documentation © 2025 Ticket Tracking System Team. All rights reserved.

---

**Last Updated**: 2025-11-19  
**Documentation Maintainer**: System Architecture Team
