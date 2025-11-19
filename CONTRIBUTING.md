# Contributing to Ticket Tracking System

Thank you for your interest in contributing to the Ticket Tracking System! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Security](#security)

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inspiring community for all. Please be respectful and professional in all interactions.

### Expected Behavior
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git
- PostgreSQL 15+ (for local development without Docker)

### Initial Setup
1. **Fork the Repository**
   ```bash
   # Click "Fork" button on GitHub
   git clone https://github.com/YOUR_USERNAME/Ticket-Tracking-System.git
   cd Ticket-Tracking-System
   ```

2. **Add Upstream Remote**
   ```bash
   git remote add upstream https://github.com/Gknightt/Ticket-Tracking-System.git
   ```

3. **Set Up Development Environment**
   ```bash
   # Using Docker (recommended)
   bash ./Scripts/docker.sh
   
   # Or manually for each service
   cd auth
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

4. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Development Workflow

### 1. Create a Branch
Always create a new branch for your work:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
# or
git checkout -b docs/documentation-update
```

**Branch Naming Conventions**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks

### 2. Make Your Changes
- Keep changes focused and atomic
- Follow the coding standards (see below)
- Write tests for new functionality
- Update documentation as needed

### 3. Test Your Changes
```bash
# Backend tests
cd auth  # or ticket_service, workflow_api, etc.
python manage.py test

# Frontend tests
cd frontend
npm test

# Docker integration test
bash ./Scripts/docker.sh
```

### 4. Commit Your Changes
```bash
git add .
git commit -m "descriptive commit message"
```

### 5. Keep Your Branch Updated
```bash
git fetch upstream
git rebase upstream/main
```

### 6. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```
Then create a Pull Request on GitHub.

## Coding Standards

### Python (Backend)
- **Style Guide**: Follow [PEP 8](https://pep8.org/)
- **Line Length**: Maximum 120 characters
- **Imports**: Group imports (standard library, third-party, local)
- **Docstrings**: Use Google-style docstrings for functions and classes

**Example**:
```python
from typing import Optional
from rest_framework import viewsets
from rest_framework.response import Response

class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tickets.
    
    Provides CRUD operations for ticket management with proper
    authentication and authorization checks.
    """
    
    def create(self, request, *args, **kwargs):
        """
        Create a new ticket.
        
        Args:
            request: HTTP request object containing ticket data
            
        Returns:
            Response: Created ticket data with HTTP 201 status
        """
        # Implementation
        pass
```

### JavaScript/React (Frontend)
- **Style Guide**: Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- **Components**: Use functional components with hooks
- **Naming**: PascalCase for components, camelCase for functions/variables
- **Props**: Destructure props in component parameters

**Example**:
```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TicketList = ({ userId, onTicketSelect }) => {
  const [tickets, setTickets] = useState([]);
  
  useEffect(() => {
    fetchTickets();
  }, [userId]);
  
  const fetchTickets = async () => {
    try {
      const response = await axios.get(`/api/tickets?user=${userId}`);
      setTickets(response.data);
    } catch (error) {
      console.error('Error fetching tickets:', error);
    }
  };
  
  return (
    <div className="ticket-list">
      {tickets.map(ticket => (
        <TicketCard key={ticket.id} ticket={ticket} onClick={onTicketSelect} />
      ))}
    </div>
  );
};

export default TicketList;
```

### Django Best Practices
- Use class-based views or ViewSets for REST APIs
- Implement proper serializers for all API responses
- Use Django ORM (avoid raw SQL)
- Implement proper permission classes
- Use environment variables for configuration (never hardcode secrets)

### Database
- Always create migrations: `python manage.py makemigrations`
- Write descriptive migration names when possible
- Test migrations on a copy of production data
- Never delete migrations that have been deployed

## Testing Guidelines

### Backend Testing
**Location**: Each service has a `tests/` directory or `tests.py` file

**Types of Tests**:
- **Unit Tests**: Test individual functions/methods
- **Integration Tests**: Test service interactions
- **API Tests**: Test endpoint behavior

**Example Test**:
```python
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

class TicketAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_ticket(self):
        """Test ticket creation via API"""
        data = {
            'title': 'Test Ticket',
            'description': 'Test description',
            'priority': 'high'
        }
        response = self.client.post('/api/tickets/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Ticket')
```

### Frontend Testing
- Write tests for components with significant logic
- Test user interactions and API calls
- Use React Testing Library best practices

### Test Coverage
- Aim for >80% code coverage
- All new features must include tests
- Bug fixes should include regression tests

## Commit Messages

### Format
```
type(scope): brief description

Detailed explanation of the changes made (optional)

Fixes #123
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(auth): add JWT refresh token functionality

Implements automatic token refresh when access token expires.
Includes new endpoint /api/token/refresh/ and client-side logic.

Fixes #456
```

```
fix(tickets): resolve file upload size limit issue

Increased max file size from 5MB to 10MB and added proper
error messaging when limit is exceeded.

Fixes #789
```

## Pull Request Process

### Before Submitting
1. ✅ All tests pass locally
2. ✅ Code follows style guidelines
3. ✅ Documentation is updated
4. ✅ Commit messages are clear
5. ✅ Branch is up-to-date with main

### PR Template
When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Dependent changes merged
```

### Review Process
1. **Automated Checks**: GitHub Actions will run tests and linting
2. **Code Review**: At least one maintainer must approve
3. **Security Scan**: No critical vulnerabilities
4. **Documentation**: Required for user-facing changes
5. **Merge**: Squash and merge (default) or rebase

### After PR is Merged
- Delete your branch: `git branch -d feature/your-feature-name`
- Update your fork: `git pull upstream main`

## Documentation

### When to Update Documentation
- New features or endpoints
- Changes to existing behavior
- Configuration changes
- Deployment procedures

### Documentation Files
- `docs/` - Main documentation
- `ReadMe.md` - Quick start guide
- Inline code comments - Complex logic
- API documentation - All endpoints

### Docstring Example
```python
def calculate_ticket_priority(urgency: int, impact: int) -> str:
    """
    Calculate ticket priority based on urgency and impact.
    
    Priority is calculated using a matrix:
    - High urgency + High impact = Critical
    - High urgency + Low impact = High
    - Low urgency + High impact = Medium
    - Low urgency + Low impact = Low
    
    Args:
        urgency (int): Urgency level (1-5)
        impact (int): Impact level (1-5)
        
    Returns:
        str: Priority level ('critical', 'high', 'medium', 'low')
        
    Raises:
        ValueError: If urgency or impact is out of range
    """
    # Implementation
```

## Security

### Reporting Vulnerabilities
**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email security concerns to: [security email - to be added]
2. Use GitHub's private vulnerability reporting feature
3. Provide detailed description and reproduction steps

### Security Best Practices
- Never commit secrets (API keys, passwords, etc.)
- Use environment variables for sensitive data
- Validate all user inputs
- Use parameterized queries (Django ORM handles this)
- Keep dependencies updated
- Run security scans before submitting PRs

### Dependencies
Before adding new dependencies:
```bash
# Check for vulnerabilities
pip-audit
npm audit

# Or use the gh-advisory-database tool (if available)
```

## Questions?

- **Documentation**: Check [docs/](./docs/) directory
- **Discussions**: Use GitHub Discussions
- **Issues**: Search existing issues before creating new ones
- **Chat**: [Add Slack/Discord link if available]

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Ticket Tracking System! 🎉
