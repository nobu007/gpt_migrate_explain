# Architecture Check Command

Automated architecture compliance checking using SDEC×2SCV×ACR framework.

## Description

Runs comprehensive architecture analysis to ensure codebase adherence to clean architecture principles and SOLID guidelines. Checks for:
- Single Responsibility Principle violations
- Circular dependencies  
- Layer violations (clean architecture)
- Import violations
- Naming convention violations
- Complexity violations

## Usage

```bash
/architecture-check [path] [--output file] [--format text|json]
```

### Arguments

- **path** (optional): Path to analyze (default: current directory)
- **--output**, **-o** (optional): Output report file (default: stdout)
- **--format** (optional): Report format - text or json (default: text)

## Examples

Check current directory architecture compliance:
```bash
/architecture-check
```

Check specific path and save report:
```bash
/architecture-check backend/ --output architecture-report.md
```

Generate JSON report for CI/CD:
```bash
/architecture-check . --format json --output compliance-report.json
```

## Output

The command generates a comprehensive report including:
- Overall compliance score (0-100)
- Violations grouped by severity and type
- Specific actionable recommendations
- Detailed violation descriptions with line numbers

### Exit Codes

- **0**: Compliance score >= 80 (good)
- **1**: Compliance score < 80 (needs improvement)

## Integration

Can be integrated into CI/CD pipelines:

```yaml
- name: Architecture Compliance Check
  run: |
    /architecture-check . --format json --output compliance-report.json
    # Fail build if compliance score is too low
    score=$(cat compliance-report.json | jq '.overall_compliance_score')
    if (( $(echo "$score < 80" | bc -l) )); then
      echo "Architecture compliance too low: $score"
      exit 1
    fi
```

## Framework

Implements SDEC×2SCV×ACR methodology:
- **Spec**: Define architecture rules and thresholds
- **Data**: Collect evidence from codebase analysis  
- **Eval**: Validate evidence against architectural principles
- **Change**: Provide actionable improvement recommendations
- **ACR**: Autonomous context reconstruction for complex patterns