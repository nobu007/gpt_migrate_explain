# Agent Workflow Patterns

This document describes common workflow patterns used by agents in the Miyabi framework.

## Universal Workflow Pattern

All agents follow a similar workflow structure:

1. **Initial Assessment** - Analyze current state and requirements
2. **Execution** - Apply specialized expertise using available tools
3. **Validation** - Verify results meet quality standards
4. **Reporting** - Provide clear recommendations and next steps

## Type-Specific Workflow Patterns

### Code Review Workflow

#### Phase 1: Architecture & Design Analysis (25%)
```
1. Examine overall project structure
2. Identify design patterns used
3. Evaluate SOLID principles adherence
4. Assess modularity and separation of concerns
5. Review dependency management
6. Check for architectural anti-patterns
```

#### Phase 2: Code Quality Assessment (20%)
```
1. Review code readability and style
2. Check for code smells and technical debt
3. Evaluate error handling patterns
4. Assess variable and function naming
5. Review code documentation
6. Check for duplication and redundancy
```

#### Phase 3: Security & Dependencies (20%)
```
1. Scan for OWASP Top 10 vulnerabilities
2. Check dependency versions and security
3. Validate input sanitization
4. Review authentication/authorization
5. Check for hardcoded secrets
6. Assess data validation practices
```

#### Phase 4: Performance & Scalability (15%)
```
1. Analyze algorithmic complexity
2. Identify performance bottlenecks
3. Check resource management
4. Assess database query efficiency
5. Review memory usage patterns
6. Evaluate scalability considerations
```

#### Phase 5: Testing Coverage (10%)
```
1. Analyze test coverage metrics
2. Review test quality and effectiveness
3. Check for missing edge cases
4. Evaluate test structure
5. Assess integration testing
6. Review test documentation
```

#### Phase 6: Documentation & API Design (10%)
```
1. Review API design consistency
2. Check documentation completeness
3. Evaluate code comments
4. Assess user-facing docs
5. Review inline documentation
6. Check example code quality
```

---

### Deployment Workflow

#### Phase 1: Pre-deployment Validation
```
1. Verify all tests pass with required coverage
2. Check build artifacts and dependencies
3. Validate environment configurations
4. Review deployment checklist
5. Confirm rollback procedures are ready
6. Check monitoring and alerting setup
```

#### Phase 2: Deployment Execution
```
1. Execute deployment pipeline
2. Monitor deployment progress
3. Track deployment metrics
4. Handle deployment failures
5. Coordinate with dependent services
6. Document deployment process
```

#### Phase 3: Health Check & Monitoring
```
1. Perform comprehensive health checks
2. Monitor key performance metrics
3. Check service functionality
4. Verify performance thresholds
5. Test user workflows
6. Validate integrations
```

#### Phase 4: Rollback Management
```
1. Monitor rollback triggers
2. Prepare rollback procedures
3. Execute rollback when necessary
4. Document rollback reasons
5. Analyze rollback impact
6. Update monitoring configurations
```

#### Phase 5: Post-deployment Tasks
```
1. Update deployment status
2. Notify stakeholders
3. Document issues and improvements
4. Update monitoring configurations
5. Archive deployment artifacts
6. Plan next deployment cycle
```

---

### Testing Workflow

#### Phase 1: Test Planning
```
1. Analyze requirements and scope
2. Identify test types needed
3. Plan test data and environments
4. Define success criteria
5. Create test timelines
6. Resource allocation planning
```

#### Phase 2: Test Execution
```
1. Run unit tests with coverage verification
2. Execute integration tests
3. Perform end-to-end testing
4. Run security tests
5. Execute performance tests
6. Validate accessibility requirements
```

#### Phase 3: Test Analysis
```
1. Analyze test results and coverage
2. Identify failing tests and root causes
3. Assess test quality metrics
4. Evaluate test effectiveness
5. Review test performance
6. Identify test gaps
```

#### Phase 4: Quality Validation
```
1. Verify code quality standards
2. Check for security vulnerabilities
3. Validate performance benchmarks
4. Ensure documentation completeness
5. Review compliance requirements
6. Assess user experience metrics
```

#### Phase 5: Reporting
```
1. Generate comprehensive test reports
2. Provide quality recommendations
3. Identify improvement areas
4. Document test automation status
5. Create action plans for issues
6. Archive test artifacts and results
```

---

### Documentation Workflow

#### Phase 1: Documentation Analysis
```
1. Analyze existing codebase structure
2. Identify documentation gaps
3. Review current documentation quality
4. Assess target audience needs
5. Evaluate documentation tools
6. Check version control integration
```

#### Phase 2: Content Generation
```
1. Generate API documentation from code
2. Create comprehensive README files
3. Develop technical guides
4. Produce code examples
5. Create usage tutorials
6. Write troubleshooting guides
```

#### Phase 3: Documentation Structure
```
1. Organize documentation logically
2. Ensure consistent formatting
3. Create proper navigation
4. Add cross-references
5. Maintain version compatibility
6. Implement search functionality
```

#### Phase 4: Quality Assurance
```
1. Verify technical accuracy
2. Check for completeness
3. Validate examples and code
4. Ensure current information
5. Test documentation instructions
6. Review accessibility
```

#### Phase 5: Maintenance Planning
```
1. Establish update workflows
2. Plan regular review cycles
3. Coordinate with development teams
4. Monitor documentation usage
5. Collect user feedback
6. Implement continuous updates
```

---

### Security Workflow

#### Phase 1: Security Scanning
```
1. Perform comprehensive code scans
2. Check against OWASP Top 10
3. Analyze dependency security
4. Scan for hardcoded secrets
5. Review authentication mechanisms
6. Check data handling practices
```

#### Phase 2: Threat Analysis
```
1. Identify potential security threats
2. Assess attack surfaces
3. Evaluate security controls
4. Review incident response plans
5. Analyze security monitoring
6. Assess compliance requirements
```

#### Phase 3: Compliance Validation
```
1. Check regulatory compliance
2. Validate security policies
3. Review audit requirements
4. Assess documentation completeness
5. Verify security training
6. Check certification status
```

#### Phase 4: Risk Assessment
```
1. Categorize security risks
2. Provide remediation recommendations
3. Estimate exploitability
4. Assess potential impact
5. Prioritize security improvements
6. Create mitigation plans
```

#### Phase 5: Security Reporting
```
1. Generate detailed security reports
2. Provide actionable remediation steps
3. Document security findings
4. Create improvement recommendations
5. Establish security metrics
6. Plan security initiatives
```

---

### General Purpose Workflow

#### Phase 1: Requirement Analysis
```
1. Understand task objectives
2. Identify constraints and limitations
3. Plan approach and methodology
4. Define success criteria
5. Gather necessary resources
6. Establish timelines
```

#### Phase 2: Information Gathering
```
1. Research relevant information
2. Analyze existing codebase
3. Gather context from sources
4. Validate information accuracy
5. Identify knowledge gaps
6. Document findings
```

#### Phase 3: Problem Decomposition
```
1. Break complex tasks into steps
2. Identify dependencies
3. Plan execution sequence
4. Prepare contingency approaches
5. Allocate resources
6. Define milestones
```

#### Phase 4: Execution & Coordination
```
1. Execute planned steps systematically
2. Coordinate with other agents
3. Adapt approach based on findings
4. Handle unexpected issues
5. Document progress
6. Maintain communication
```

#### Phase 5: Synthesis & Reporting
```
1. Synthesize findings and results
2. Generate comprehensive reports
3. Provide actionable recommendations
4. Document lessons learned
5. Create follow-up plans
6. Share knowledge and insights
```

---

## Workflow Quality Standards

### Common Quality Criteria

All agent workflows should meet these standards:

1. **Clarity**: Steps are clearly defined and unambiguous
2. **Completeness**: All necessary phases are included
3. **Actionability**: Each step produces concrete results
4. **Measurability**: Progress and success can be measured
5. **Adaptability**: Workflow can handle edge cases
6. **Documentation**: Each step is properly documented

### Error Handling Patterns

```markdown
1. **Input Validation**
   - Verify all inputs before processing
   - Handle malformed or incomplete data
   - Provide clear error messages

2. **Exception Handling**
   - Catch and handle expected exceptions
   - Log unexpected errors appropriately
   - Implement graceful degradation

3. **Recovery Procedures**
   - Define rollback strategies
   - Implement retry mechanisms
   - Provide alternative approaches

4. **Error Reporting**
   - Generate clear error reports
   - Include context and debugging info
   - Suggest remediation steps
```

### Performance Optimization

```markdown
1. **Efficient Tool Usage**
   - Minimize unnecessary tool calls
   - Use appropriate tools for each task
   - Batch related operations

2. **Resource Management**
   - Monitor memory and CPU usage
   - Implement caching where appropriate
   - Clean up temporary resources

3. **Parallel Processing**
   - Identify independent tasks
   - Execute in parallel when possible
   - Coordinate parallel results
```

---

*This workflow patterns document is part of the agent-creator skill*