# Agent Types Reference

This document describes the available agent types and their characteristics for the agent-creator skill.

## Available Agent Types

### 1. Code Review Agent (`code-review`)

**Purpose**: Comprehensive code review specialist covering multiple quality aspects.

**Key Characteristics**:
- Architecture & design analysis
- Code quality assessment
- Security vulnerability detection
- Performance & scalability evaluation
- Testing coverage analysis
- Documentation & API design review

**Typical Use Cases**:
- Post-commit code reviews
- Pre-merge quality gates
- Architecture decision validation
- Security audit preparation
- Performance bottleneck identification

**Weight Distribution**:
- Architecture & Design: 25%
- Code Quality: 20%
- Security & Dependencies: 20%
- Performance & Scalability: 15%
- Testing Coverage: 10%
- Documentation & API Design: 10%

**Quality Score Requirements**: 80+ points for progression

---

### 2. Deployment Agent (`deployment`)

**Purpose**: CI/CD automation specialist with deployment pipeline management.

**Key Characteristics**:
- Automated deployment execution
- Health check monitoring
- Automatic rollback functionality
- Environment configuration management
- Deployment validation

**Typical Use Cases**:
- Production deployments
- Staging environment updates
- Rollback procedures
- Health monitoring
- Environment provisioning

**Workflow Stages**:
1. Pre-deployment validation
2. Deployment execution
3. Health check & monitoring
4. Rollback management
5. Post-deployment tasks

**Integration Points**:
- CoordinatorAgent for task delegation
- CI/CD pipelines
- Monitoring systems
- Notification services

---

### 3. Testing Agent (`testing`)

**Purpose**: Test automation and coverage analysis specialist.

**Key Characteristics**:
- Automated test execution
- Coverage report generation
- Test result analysis
- Quality assurance validation
- Performance testing

**Typical Use Cases**:
- Unit test execution
- Integration testing
- End-to-end testing
- Coverage analysis
- Quality gate validation

**Coverage Requirements**:
- Minimum 80% test coverage
- All critical paths tested
- Edge cases covered
- Error handling verified

**Test Types**:
- Unit tests
- Integration tests
- API tests
- End-to-end tests
- Security tests
- Performance tests

---

### 4. Documentation Agent (`documentation`)

**Purpose**: Documentation generation and maintenance specialist.

**Key Characteristics**:
- API documentation generation
- README creation
- Code documentation analysis
- Technical writing assistance
- Documentation maintenance

**Typical Use Cases**:
- API documentation generation
- README file creation
- Technical guide development
- Code comment analysis
- Documentation maintenance

**Documentation Types**:
- API reference documentation
- User guides and tutorials
- Technical specifications
- Code documentation
- Architecture documentation
- Process documentation

**Quality Standards**:
- Technical accuracy
- Completeness and clarity
- Consistent formatting
- Current and up-to-date
- Target audience appropriate

---

### 5. Security Agent (`security`)

**Purpose**: Security analysis and vulnerability assessment specialist.

**Key Characteristics**:
- Security vulnerability scanning
- OWASP Top 10 analysis
- Code security review
- Dependency security analysis
- Security best practices validation

**Typical Use Cases**:
- Security audits
- Vulnerability assessments
- Code security reviews
- Dependency analysis
- Compliance validation

**Security Frameworks**:
- OWASP Top 10
- SANS Top 25
- CVE database
- Security best practices
- Industry standards

**Risk Categories**:
- Critical (Immediate action required)
- High (Address within 24 hours)
- Medium (Address within 1 week)
- Low (Address in next release)

---

### 6. General Purpose Agent (`general-purpose`)

**Purpose**: General-purpose agent for research and complex multi-step tasks.

**Key Characteristics**:
- Complex research tasks
- Information gathering
- Multi-step task coordination
- Problem analysis
- Solution development

**Typical Use Cases**:
- Research projects
- Complex problem solving
- Information synthesis
- Multi-step workflows
- Cross-functional coordination

**Tool Access**: All tools available (*)

**Workflow Patterns**:
1. Requirement analysis
2. Information gathering
3. Problem decomposition
4. Execution & coordination
5. Synthesis & reporting

---

## Agent Selection Guidelines

### When to Use Each Agent Type

| Situation | Recommended Agent | Rationale |
|-----------|------------------|-----------|
| Code review needed | `code-review` | Specialized quality analysis across multiple dimensions |
| Deployment pipeline | `deployment` | Automation expertise and rollback capabilities |
| Testing requirements | `testing` | Coverage analysis and quality assurance focus |
| Documentation gaps | `documentation` | Technical writing and documentation generation |
| Security concerns | `security` | Vulnerability scanning and security best practices |
| Complex research | `general-purpose` | Broad tool access and research capabilities |
| Unknown requirements | `general-purpose` | Flexible and adaptable to various tasks |

### Agent Combination Patterns

1. **Code Quality Pipeline**: `code-review` → `testing` → `security`
   - Comprehensive quality assessment
   - Sequential validation stages
   - Multiple quality gates

2. **Release Pipeline**: `testing` → `security` → `deployment`
   - Quality assurance first
   - Security validation before deployment
   - Automated deployment execution

3. **Documentation Update**: `documentation` → `code-review`
   - Generate documentation
   - Review for accuracy and completeness

4. **Research & Implementation**: `general-purpose` → specific agent
   - Research and analysis
   - Specialized implementation

---

## Agent Development Guidelines

### Creating New Agent Types

When extending the agent system:

1. **Define Clear Purpose**: What specific problem does this agent solve?
2. **Identify Capabilities**: What specific skills and tools are needed?
3. **Design Workflow**: What steps should the agent follow?
4. **Set Quality Standards**: How do we measure success?
5. **Integration Points**: How does it work with other agents?

### Agent Quality Standards

All agents should:

- Maintain 80+ quality score threshold
- Provide clear, actionable feedback
- Follow established coding standards
- Document significant decisions
- Ensure security best practices
- Include error handling
- Validate inputs and outputs

### Agent Naming Conventions

- Use descriptive, purpose-driven names
- Include "agent" suffix for clarity
- Use kebab-case for multi-word names
- Examples: `code-review-expert`, `security-analyzer`, `deployment-automator`

---

## Agent Configuration

### Environment Variables

Agents can be configured using environment variables:

```bash
# General configuration
AGENT_DEBUG=false
AGENT_LOG_LEVEL=info
AGENT_TIMEOUT=300

# Agent-specific configuration
CODE_REVIEW_STRICT_MODE=true
SECURITY_SCAN_DEPTH=deep
TESTING_COVERAGE_THRESHOLD=80
```

### Tool Access Control

Agent tool access can be restricted:

```yaml
# Limited tool access example
tools:
  - Read
  - Grep
  - Glob
  - Bash
```

### Quality Thresholds

Configure quality requirements per agent type:

```yaml
# Example quality thresholds
code_review:
  min_score: 85
  security_weight: 0.3

testing:
  min_coverage: 80
  critical_path_coverage: 95

deployment:
  health_check_timeout: 300
  rollback_threshold: 3
```

---

*This reference document is part of the agent-creator skill*