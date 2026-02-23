---
type: reference
---

# Spring Boot Development Guidelines [source: instructions/springboot.instructions.md]

Guidelines for building Spring Boot base applications, focusing on best practices and maintainability.

## Configuration Options
- `application.yml`: Externalized configuration file
- `@ConfigurationProperties`: Type-safe configuration binding
- Environment Profiles: Use Spring profiles for different environments (dev, test, prod)
- Secrets Management: Externalize secrets using environment variables or secret management systems

## Code Organization
- Package Structure: Organize by feature/domain rather than by layer
- Separation of Concerns: Keep controllers thin, services focused, and repositories simple
- Utility Classes: Make utility classes final with private constructors

## Service Layer
- `@Service`-annotated classes: Place business logic
- Services should be stateless and testable
- Inject repositories via the constructor
- Service method signatures should use domain IDs or DTOs, not expose repository entities directly unless necessary

## Logging
- SLF4J for all logging (`private static final Logger logger = LoggerFactory.getLogger(MyClass.class);`)
- Do not use concrete implementations (Logback, Log4j2) or `System.out.println()` directly
- Use parameterized logging: `logger.info("User {} logged in", userId);`

## Security & Input Handling
- Parameterized queries: Prevent SQL injection using Spring Data JPA or `NamedParameterJdbcTemplate`
- Validate request bodies and parameters using JSR-380 (`@NotNull`, `@Size`, etc.) annotations and `BindingResult`

## Build and Verification
- After adding or modifying code, verify the project continues to build successfully.
- If the project uses Maven, run `mvn clean package`.
- If the project uses Gradle, run `./gradlew build` (or `gradlew.bat build` on Windows).
- Ensure all tests pass as part of the build.

## Useful Commands
| Command                | Description                                   |
|:-----------------------|:----------------------------------------------|
| `./gradlew bootRun`    | Run the application.                          |
| `./gradlew build`      | Build the application.                        |
| `./gradlew test`       | Run tests.                                    |
| `./gradlew bootJar`    | Package the application as a JAR.             |
| `./gradlew bootBuildImage` | Package the application as a container image. |