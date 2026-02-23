---
type: reference
---

# Multi-Platform Feature Development Workflow

Build and deploy the same feature consistently across web, mobile, and desktop platforms using API-first architecture and parallel implementation strategies.

[Extended thinking: This workflow orchestrates multiple specialized agents to ensure feature parity across platforms while maintaining platform-specific optimizations. The coordination strategy emphasizes shared contracts and parallel development with regular synchronization points. By establishing API contracts and data models upfront, teams can work independently while ensuring consistency. The workflow benefits include faster time-to-market, reduced integration issues, and maintainable cross-platform codebases.]

## Phase 1: Architecture and API Design (Sequential)

### 1. Define Feature Requirements and API Contracts
- Use Task tool with subagent_type="backend-architect"
- Prompt: "Design the API contract for feature: [user-defined]. Create OpenAPI 3.1 specification with:
  - RESTful endpoints with proper HTTP methods and status codes
  - GraphQL schema if applicable for complex data queries
  - WebSocket events for real-time features
  - Request/response schemas with validation rules
  - Authentication and authorization requirements
  - Rate limiting and caching strategies
  - Error response formats and codes
  Define shared data models that all platforms will consume."
- Expected output: Complete API specification, data models, and integration guidelines [source: multi-platform-apps/commands/multi-platform.md]

### 2. Design System and UI/UX Consistency
- Use Task tool with subagent_type="ui-ux-designer"
- Prompt: "Create cross-platform design system for feature using API spec: [previous output]. Include:
  - Component specifications for each platform (Material Design, iOS HIG, Fluent)
  - Responsive layouts for web (mobile-first approach)
  - Native patterns for iOS (SwiftUI) and Android (Material You)
  - Desktop-specific considerations (keyboard shortcuts, window management)
  - Accessibility requirements (WCAG 2.2 Level AA)
  - Dark/light theme specifications
  - Animation and transition guidelines"
- Context from previous: API endpoints, data structures, authentication flows [source: multi-platform-apps/commands/multi-platform.md]
- Expected output: Design system documentation, component library specs, platform guidelines

### 3. Shared Business Logic Architecture
- Use Task tool with subagent_type="comprehensive-review::architect-review"
- Prompt: "Design shared business logic architecture for cross-platform feature. Define:
  - Core domain models and entities (platform-agnostic)
  - Business rules and validation logic
  - State management patterns (MVI/Redux/BLoC)
  - Caching and offline strategies
  - Error handling and retry policies
  - Platform-specific adapter patterns
  Consider Kotlin Multiplatform for mobile or TypeScript for web/desktop sharing."
- Context from previous: API contracts, data models, UI requirements [source: multi-platform-apps/commands/multi-platform.md]
- Expected output: Shared code architecture, platform abstraction layers, implementation guide

## Phase 2: Parallel Platform Implementation

### 4a. Web Implementation (React/Next.js)
- Use Task tool with subagent_type="frontend-developer"
- Prompt: "Implement web version of feature using:
  - React 18+ with Next.js 14+ App Router
  - TypeScript for type safety
  - TanStack Query for API: [API spec]
  - Zustand/Redux Toolkit for state management
  - Tailwind CSS with design system: [design specs]
  - Progressive Web App capabilities
  - SSR/SSG optimization where appropriate
  - Web vitals optimization (LCP < 2.5s, FID < 100ms)
  Follow shared business logic: [architecture doc]"
- Context from previous: API contracts, design system, shared logic patterns [source: multi-platform-apps/commands/multi-platform.md]
- Expected output: Complete web implementation with tests

### 4b. iOS Implementation (SwiftUI)
- Use Task tool with subagent_type="ios-developer"
- Prompt: "Implement iOS version using:
  - SwiftUI with iOS 17+ features
  - Swift 5.9+ with async/await
  - URLSession with Combine for API: [API spec]
  - Core Data/SwiftData for persistence
  - Design system compliance: [iOS HIG specs]
  - Widget extensions if applicable
  - Platform-specific features (Face ID, Haptics, Live Activities)
  - Testable MVVM architecture
  Follow shared patterns: [architecture doc]"
- Context from previous: API contracts, iOS design guidelines, shared models [source: multi-platform-apps/commands/multi-platform.md]
- Expected output: Native iOS implementation with unit/UI tests

### 4c. Android Implementation (Kotlin/Compose)
- Use Task tool with subagent_type="mobile-developer"
- Prompt: "Implement Android version using:
  - Jetpack Compose with Material 3
  - Kotlin coroutines and Flow
  - Retrofit/Ktor for API: [API spec]
  - Room database for local storage
  - Hilt for dependency injection
  - Material You dynamic theming: [design specs]
  - Platform features (biometric auth, widgets)
  - Clean architecture with MVI pattern
  Follow shared business logic: [architecture doc]"
- Context from previous: API contracts, Android design guidelines, shared models [source: multi-platform-apps/commands/multi-platform.md]
- Expected output: Optimized Android implementation with tests

## Configuration Options

- **--platforms**: Specify target platforms (web,ios,android,desktop)
- **--api-first**: Generate API before UI implementation (default: true)
- **--shared-code**: Use Kotlin Multiplatform or similar (default: evaluate)
- **--design-system**: Use existing or create new (default: create)
- **--testing-strategy**: Unit, integration, e2e (default: all)

## Success Criteria

- API contract defined and validated before implementation
- All platforms achieve feature parity with <5% variance
- Performance metrics meet platform-specific standards
- Accessibility standards met (WCAG 2.2 AA minimum)
- Cross-platform testing shows consistent behavior
- Documentation complete for all platforms
- Code reuse >40% between platforms where applicable
- User experience optimized for each platform's conventions

## Platform-Specific Considerations

**Web**: PWA capabilities, SEO optimization, browser compatibility
**iOS**: App Store guidelines, TestFlight distribution, iOS-specific features
**Android**: Play Store requirements, Android App Bundles, device fragmentation
**Desktop**: Code signing, auto-updates, OS-specific installers

Initial feature specification: [user-defined]

## Instructions
1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim, do not summarize)
3. Add a citation [source: multi-platform-apps/commands/multi-platform.md] at the end
4. Ensure all headings follow a logical hierarchy (no skipping levels)
5. Expand any placeholder text like [user-defined] into helpful descriptions
6. Start with YAML frontmatter including title, description, and tags
7. Do NOT wrap the output in a markdown code block (output raw text)
8. Do not repeat these instructions in your response.