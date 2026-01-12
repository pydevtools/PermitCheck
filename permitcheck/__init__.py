__name__ = "PermitCheck"
__version__ = "2.0.0"
__summary__ = "PermitCheck: A Multi-Language License Compliance Checker"

__description__ = """
PermitCheck is a cross-platform tool designed to ensure license compliance across 
multiple programming languages by analyzing dependencies and enforcing predefined 
license policies. 

PermitCheck helps maintain legal standards by scanning the project's dependencies and 
ensuring that only approved licenses (e.g., MIT, Apache 2.0) are used.
"""

__features__ = """
Cross-Language License Checking: 
    PermitCheck is designed to support multiple languages, providing static license checking for Python, 
    with plans to support other languages like JavaScript, Java, Ruby, and more in the future.

Flexible Integration: 
    Integrates smoothly into various build systems and CI/CD pipelines, ensuring that license compliance 
    is enforced across all stages of development.

Support and Beyond: 
    With initial support for Python projects (using Poetry or pip), PermitCheck will extend to other package managers 
    like npm (package.json), Maven (pom.xml), and others.

Customizable License Policies: 
    Users can configure the tool to accept or reject specific licenses, making it adaptable to different 
    legal requirements or organizational policies.

Comprehensive License Auditing: 
    PermitCheck generates detailed reports on non-compliant dependencies, offering insights into 
    potential legal risks.

Extensibility: 
    Built to be extensible so developers can add new language support or custom rules for specific license scenarios.
"""