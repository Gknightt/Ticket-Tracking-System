## **Ticket Tracking System**

### **Overview**
The Ticket Tracking System is a comprehensive platform designed to manage and streamline ticketing workflows for organizations. It integrates multiple services, including user authentication, ticket management, workflow automation, and frontend interfaces for both administrators and agents. The system is built using a microservices architecture, leveraging technologies like Django, React, RabbitMQ, PostgreSQL, and Celery for asynchronous task processing.

---

### **Key Features**
1. **Ticket Management**:
   - Create, update, and track tickets.
   - Categorize tickets by priority, status, and department.
   - Attach files and manage ticket metadata.

2. **Workflow Automation**:
   - Automate task allocation based on ticket attributes.
   - Track ticket progress through various workflow stages.

3. **User Roles**:
   - Admins: Manage tickets, assign tasks, and oversee workflows.
   - Agents: Handle assigned tickets and provide resolutions.

4. **Frontend Interface**:
   - React-based UI for both admin and agent dashboards.
   - Real-time updates and notifications.

5. **Backend Services**:
   - Django-based microservices for ticket, workflow, and user management.
   - RabbitMQ for message queuing and Celery for task processing.

6. **Database**:
   - PostgreSQL for storing ticket, workflow, and user data.

---

### **System Architecture**
The system is divided into the following services:
- **User Service**: Handles user authentication and role management.
- **Ticket Service**: Manages ticket creation, updates, and metadata.
- **Workflow API**: Automates workflows and tracks ticket progress.
- **Frontend**: Provides a user-friendly interface for admins and agents.
- **RabbitMQ**: Facilitates communication between services.
- **PostgreSQL**: Centralized database for all services.

---

### **Technologies Used**
- **Backend**: Django, Django REST Framework
- **Frontend**: React, Vite
- **Message Queue**: RabbitMQ
- **Database**: PostgreSQL
- **Task Queue**: Celery
- **Containerization**: Docker, Docker Compose

---

### **Setup Instructions**
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd Ticket-Tracking-System
   ```

2. **Run the Docker Starter Script**:
   ```bash
   bash ./Scripts/docker.sh
   ```

3. **Access the Services**:
   - Frontend: [http://localhost:1000](http://localhost:1000)
   - Admin Panel: [http://localhost:8001/admin](http://localhost:8001/admin)
   - RabbitMQ Management: [http://localhost:15672](http://localhost:15672)

4. **Run Migrations**:
   ```bash
   docker exec -it <service_name> python manage.py migrate
   ```

5. **Seed Data (Optional)**:
   ```bash
   docker exec -it <service_name> python manage.py seed_tickets
   ```

---

### **Documentation**

Comprehensive documentation is available in the [`docs/`](./docs/) directory:

#### **Core Documentation**
- **[Deployment & Infrastructure](./docs/deployment-infrastructure.md)** - Deployment strategy, Docker configuration, server specifications, and containerization details
- **[Security Measures](./docs/security-measures.md)** - Authentication (JWT), authorization (RBAC), encryption, and API security
- **[DevOps & CI/CD](./docs/devops-cicd.md)** - CI/CD pipeline, GitHub Actions workflows, automated testing, and deployment automation
- **[Licensing & Open Source](./docs/licensing-opensource.md)** - License information, dependency list, compliance procedures

#### **Quick Links**
- [Documentation Index](./docs/README.md) - Complete documentation overview
- [Environment Variables](./ENVIRONMENT_STANDARDIZATION_REPORT.md) - Configuration reference
- [Rate Limiting](./RATE_LIMITING_IMPLEMENTATION.md) - API rate limiting details

---

### **Contributing**

We welcome contributions! Please follow these guidelines:

1. **Fork the Repository**: Create your own fork of the project
2. **Create a Branch**: `git checkout -b feature/your-feature-name`
3. **Make Changes**: Follow existing code style and conventions
4. **Test Thoroughly**: Ensure all tests pass
5. **Submit a Pull Request**: Describe your changes clearly

#### **Development Standards**
- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript/React
- Write tests for new features
- Update documentation as needed

#### **Code Review Process**
- All PRs require at least one approval
- CI/CD pipeline must pass
- Security scans must show no critical issues

---

### **License**

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

For information about third-party dependencies and their licenses, see [Licensing & Open Source Libraries](./docs/licensing-opensource.md).