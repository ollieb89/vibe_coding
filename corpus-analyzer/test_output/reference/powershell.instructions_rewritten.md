---
title: PowerShell Cmdlet Development Guidelines
source: instructions/powershell.instructions.md
---

### Content
---
applyTo: '**/*.ps1,**/*.psm1'
description: 'PowerShell cmdlet and scripting best practices based on Microsoft guidelines'
---

# PowerShell Cmdlet Development Guidelines

This guide provides PowerShell-specific instructions to help GitHub Copilot generate idiomatic, safe, and maintainable scripts. It aligns with Microsoft’s PowerShell cmdlet development guidelines.

## Naming Conventions

### Verb-Noun Format
- Use approved PowerShell verbs (Get-Verb)
- Use singular nouns
- PascalCase for both verb and noun
- Avoid special characters and spaces

### Parameter Names
- Use PascalCase
- Choose clear, descriptive names
- Use singular form unless always multiple
- Follow PowerShell standard names

### Variable Names
- Use PascalCase for public variables
- Use camelCase for private variables
- Avoid abbreviations
- Use meaningful names

### Alias Avoidance
- Use full cmdlet names
- Avoid using aliases in scripts (e.g., use Get-ChildItem instead of gci)
- Document any custom aliases
- Use full parameter names

### Example

```powershell
function Get-UserProfile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string][user-defined]sername,

        [Parameter()]
        [ValidateSet('Basic', 'Detailed')]
        [string][user-defined]rofileType = 'Basic'
    )

    process {
        # Logic here
    }
}
```
[source: instructions/powershell.instructions.md]

## Parameter Design

### Standard Parameters
- Use common parameter names (`Path`, `Name`, `Force`)
- Follow built-in cmdlet conventions
- Use aliases for specialized terms
- Document parameter purpose

### Parameter Names
- Use singular form unless always multiple
- Choose clear, descriptive names
- Follow PowerShell conventions
- Use PascalCase formatting

### Type Selection
- Use common .NET types
- Implement proper validation
- Consider ValidateSet for limited options
- Enable tab completion where possible

### Switch Parameters
- Use [switch] for boolean flags
- Avoid $true/$false parameters
- Default to $false when omitted
- Use clear action names

### Example

```powershell
function Set-UserProfile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string][user-defined]sername,

        [Parameter()]
        [switch]$Detailed
    )

    process {
        # Logic here
    }
}
```
[source: instructions/powershell.instructions.md]

## Documentation and Style

- **Comment-Based Help:** Include comment-based help for any public-facing function or cmdlet. Inside the function, add a `<# ... #>` help comment with at least:
  - `.SYNOPSIS` Brief description
  - `.DESCRIPTION` Detailed explanation
  - `.EXAMPLE` sections with practical usage
  - `.PARAMETER` descriptions
  - `.OUTPUTS` Type of output returned
  - `.NOTES` Additional information

- **Consistent Formatting:**
  - Follow consistent PowerShell style
  - Use proper indentation (4 spaces recommended)
  - Opening braces on same line as statement
  - Closing braces on new line
  - Use line breaks after pipeline operators
  - PascalCase for function and parameter names
  - Avoid unnecessary whitespace

- **Pipeline Support:**
  - Implement Begin/Process/End blocks for pipeline functions
  - Use ValueFromPipeline where appropriate
  - Support pipeline input by property name
  - Return proper objects, not formatted text

- **Avoid Aliases:** Use full cmdlet names and parameters
  - Avoid using aliases in scripts (e.g., use Get-ChildItem instead of gci); aliases are acceptable for interactive shell use.
  - Use `Where-Object` instead of `?` or `where`
  - Use `ForEach-Object` instead of `%`
  - Use `Get-ChildItem` instead of `ls` or `dir`

## Full Example: End-to-End Cmdlet Pattern

```powershell
function New-Resource {
    [CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
    param(
        [Parameter(Mandatory = $true,
            ValueFromPipeline = $true,
            ValueFromPipelineByPropertyName = $true)]
        [ValidateNotNullOrEmpty()]
        [string][user-defined]ame,

        [Parameter()]
        [ValidateSet('Development', 'Production')]
        [string][user-defined]nvironment = 'Development'
    )

    begin {
        Write-Verbose 'Starting resource creation process'
    }

    process {
        try {
            if ([user-defined]mdlet.ShouldProcess([user-defined]ame, 'Create new resource')) {
                # Resource creation logic here
                Write-Output ([PSCustomObject]@{
                        Name        = [user-defined]ame
                        Environment = [user-defined]nvironment
                        Created     = Get-Date
                    })
            }
        } catch {
            $errorRecord = [System.Management.Automation.ErrorRecord]::new(
                [user-defined].Exception,
                'ResourceCreationFailed',
                [System.Management.Automation.ErrorCategory]::NotSpecified,
                [user-defined]ame
            )
            [user-defined]mdlet.ThrowTerminatingError($errorRecord)
        }
    }

    end {
        Write-Verbose 'Completed resource creation process'
    }
}
```
[source: instructions/powershell.instructions.md]