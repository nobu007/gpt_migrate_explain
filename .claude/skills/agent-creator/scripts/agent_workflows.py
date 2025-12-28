"""Workflow definitions for different agent types"""


class AgentWorkflows:
    """Workflow definitions for different agent types"""

    WORKFLOWS = {
        "code-review": """
When performing code reviews, follow this systematic approach:

1. **Architecture & Design Analysis** (25% weight)
   - Evaluate overall architecture and design patterns
   - Check for SOLID principles adherence
   - Assess modularity and maintainability
   - Identify potential architectural improvements

2. **Code Quality Assessment** (20% weight)
   - Review code readability and style consistency
   - Check for code smells and anti-patterns
   - Evaluate error handling and edge cases
   - Assess naming conventions and documentation

3. **Security & Dependencies** (20% weight)
   - Scan for OWASP Top 10 vulnerabilities
   - Check dependency security and versions
   - Validate input sanitization and data validation
   - Review authentication and authorization

4. **Performance & Scalability** (15% weight)
   - Analyze algorithmic complexity
   - Check for performance bottlenecks
   - Evaluate memory usage and resource management
   - Assess scalability considerations

5. **Testing Coverage** (10% weight)
   - Review test coverage and quality
   - Check for missing edge case tests
   - Evaluate test structure and maintainability
   - Assess integration testing

6. **Documentation & API Design** (10% weight)
   - Review API design and consistency
   - Check documentation completeness and clarity
   - Evaluate inline code comments
   - Assess user-facing documentation

Provide specific, actionable feedback with:
- Exact file paths and line numbers
- Concrete improvement suggestions
- Code examples where helpful
- Priority levels (Critical/High/Medium/Low)
""",
        "deployment": """
For deployment automation, follow this workflow:

1. **Pre-deployment Validation**
   - Verify all tests pass with required coverage
   - Check build artifacts and dependencies
   - Validate environment configurations
   - Review deployment checklist completion

2. **Deployment Execution**
   - Execute deployment pipeline using available tools
   - Monitor deployment progress and logs
   - Handle deployment failures and rollbacks
   - Coordinate with dependent services

3. **Health Check & Monitoring**
   - Perform comprehensive health checks
   - Monitor key metrics and logs
   - Validate service functionality
   - Check performance thresholds

4. **Rollback Management**
   - Prepare rollback procedures
   - Monitor for rollback triggers
   - Execute rollback when necessary
   - Document rollback reasons and outcomes

5. **Post-deployment Tasks**
   - Update deployment status
   - Notify stakeholders
   - Document any issues or improvements
   - Update monitoring configurations
""",
        "testing": """
For test automation and quality assurance:

1. **Test Planning**
   - Analyze requirements and test scope
   - Identify test types needed (unit, integration, E2E)
   - Plan test data and environments
   - Define success criteria

2. **Test Execution**
   - Run unit tests with coverage requirements (80%+)
   - Execute integration and API tests
   - Perform end-to-end testing
   - Run security and performance tests

3. **Test Analysis**
   - Analyze test results and coverage reports
   - Identify failing tests and root causes
   - Assess test quality and effectiveness
   - Recommend test improvements

4. **Quality Validation**
   - Verify code quality standards
   - Check security vulnerabilities
   - Validate performance benchmarks
   - Ensure documentation completeness

5. **Reporting**
   - Generate comprehensive test reports
   - Provide quality recommendations
   - Identify areas needing improvement
   - Document test automation status
""",
        "documentation": """
For documentation generation and maintenance:

1. **Documentation Analysis**
   - Analyze existing codebase structure
   - Identify documentation gaps
   - Review current documentation quality
   - Assess target audience needs

2. **Content Generation**
   - Generate API documentation from code
   - Create comprehensive README files
   - Develop technical guides and tutorials
   - Produce code examples and usage patterns

3. **Documentation Structure**
   - Organize documentation logically
   - Ensure consistent formatting and style
   - Create proper navigation and cross-references
   - Maintain version compatibility information

4. **Quality Assurance**
   - Verify technical accuracy
   - Check for completeness and clarity
   - Validate examples and code snippets
   - Ensure documentation stays current

5. **Maintenance Planning**
   - Establish documentation update workflows
   - Plan for regular review cycles
   - Coordinate with development teams
   - Monitor documentation usage and feedback
""",
        "security": """
For security analysis and vulnerability assessment:

1. **Security Scanning**
   - Perform comprehensive code security scans
   - Check against OWASP Top 10 vulnerabilities
   - Analyze dependency security
   - Scan for hardcoded secrets and credentials

2. **Threat Analysis**
   - Identify potential security threats
   - Assess attack surfaces and vectors
   - Evaluate authentication and authorization
   - Review data handling and storage security

3. **Compliance Validation**
   - Check regulatory compliance requirements
   - Validate security best practices
   - Review security policies and procedures
   - Assess audit trail completeness

4. **Risk Assessment**
   - Categorize security risks by severity
   - Provide remediation recommendations
   - Estimate exploitability and impact
   - Prioritize security improvements

5. **Security Reporting**
   - Generate detailed security reports
   - Provide actionable remediation steps
   - Document security findings
   - Recommend security improvements
""",
        "general-purpose": """
For general-purpose research and complex tasks:

1. **Requirement Analysis**
   - Understand the task objectives and constraints
   - Identify necessary information and resources
   - Plan the approach and methodology
   - Define success criteria

2. **Information Gathering**
   - Research relevant information using available tools
   - Analyze existing codebase and documentation
   - Gather context from multiple sources
   - Validate information accuracy

3. **Problem Decomposition**
   - Break complex tasks into manageable steps
   - Identify dependencies and priorities
   - Plan execution sequence
   - Prepare contingency approaches

4. **Execution & Coordination**
   - Execute planned steps systematically
   - Coordinate with other agents when needed
   - Adapt approach based on findings
   - Document progress and decisions

5. **Synthesis & Reporting**
   - Synthesize findings and results
   - Generate comprehensive reports
   - Provide actionable recommendations
   - Document lessons learned
""",
    }

    @classmethod
    def get_workflow(cls, agent_type: str) -> str:
        return cls.WORKFLOWS.get(agent_type, cls.WORKFLOWS["general-purpose"])
