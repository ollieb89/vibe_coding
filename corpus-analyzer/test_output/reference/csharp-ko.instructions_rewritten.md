---
type: reference
---

# C# 코드 작성 규칙 by @jgkim999

C# 애플리케이션 개발을 위한 코드 작성 규칙입니다. Microsoft의 가이드라인을 따르는 것을 권장합니다.

## 명명 규칙 (Naming Conventions)
일관된 명명 규칙은 코드 가독성의 핵심입니다. Microsoft의 가이드라인을 따르는 것을 권장합니다.

| 요소 | 명명 규칙 | 예시 |
|------|-----------|------|
| 인터페이스 | I + PascalCase (Interface) | `IAsyncRepository`, `ILogger` |
| 공개(public) 멤버 | PascalCase (PascalCase) | `public int MaxCount;`, `public void GetData()` |
| 매개변수, 지역 변수 | camelCase (camelCase) | `int userCount`, `string customerName` |
| 비공개/내부 필드 | _ + camelCase (_camelCase) | `private string _connectionString;` |
| 상수 (const) | PascalCase (PascalCase) | `public const int DefaultTimeout = 5000;` |
| 제네릭 형식 매개변수 | T + 설명적인 이름 (TypeName) | `TKey`, `TValue`, `TResult` |
| 비동기 메서드 | Async 접미사 (AsyncSuffix) | `GetUserAsync`, `DownloadFileAsync` |

[source: instructions/csharp-ko.instructions.md]

## 코드 서식 및 가독성 (Formatting & Readability)
일관된 서식은 코드를 시각적으로 파싱하기 쉽게 만듭니다.

| 항목 | 규칙 | 설명 |
|------|------|------|
| 들여쓰기 | 4개의 공백 사용 (Indentation) | 탭 대신 4개의 공백을 사용합니다. cs 파일은 반드시 4개의 공백을 사용합니다. |
| 괄호 | 항상 중괄호 {} 사용 (Braces) | 제어문(if, for, while 등)이 한 줄이더라도 항상 중괄호를 사용합니다. |
| 빈 줄 | 논리적 분리 (Line Breaks) | 메서드 정의, 속성 정의, 논리적으로 분리된 코드 블록 사이에 빈 줄을 추가합니다. |
| 문장 작성 | 한 줄에 하나의 문장 (Sentence Per Line) | 한 줄에는 하나의 문장만 작성합니다. |
| var 키워드 | 형식이 명확할 때만 사용 (Use var sparingly) | 변수의 형식을 오른쪽에서 명확하게 유추할 수 있을 때만 var를 사용합니다. |
| 네임스페이스 | 파일 범위 네임스페이스 사용 (File-scoped Namespaces) | C# 10 이상에서는 파일 범위 네임스페이스를 사용하여 불필요한 들여쓰기를 줄입니다. |
| 주석 | XML 형식 주석 작성 (XML Comments) | 작성한 class나 함수에 항상 xml 형식의 주석을 작성합니다. |

[source: instructions/csharp-ko.instructions.md]

## 언어 기능 사용 (Language Features)
최신 C# 기능을 활용하여 코드를 더 간결하고 효율적으로 만드세요.

| 기능 | 설명 | 예시/참고 |
|------|------|------|
| 비동기 프로그래밍 | I/O 바운드 작업에 async/await 사용 (Asynchronous Programming) | `async Task<string> GetDataAsync()` |
| ConfigureAwait | 라이브러리 코드에서 컨텍스트 전환 오버헤드 감소 (Context Switching Overhead Reduction) | `await SomeMethodAsync().ConfigureAwait(false)` |
| LINQ | 컬렉션 데이터 쿼리 및 조작 (Language Integrated Query) | `users.Where(u => u.IsActive).ToList()` |
| 표현식 기반 멤버 | 간단한 메서드/속성을 간결하게 표현 (Expression-bodied Members) | `public string Name => _name;` |
| Nullable Reference Types | 컴파일 타임 NullReferenceException 방지 (Nullable Reference Types) | `#nullable enable` |
| using 선언 | IDisposable 객체의 간결한 처리 (Using Declarations) | `using var stream = new FileStream(...);` |

[source: instructions/csharp-ko.instructions.md]

## 성능 및 예외 처리 (Performance & Exception Handling)
견고하고 빠른 애플리케이션을 위한 지침입니다.

### 예외 처리

처리할 수 있는 구체적인 예외만 catch 하세요. catch (Exception)와 같이 일반적인 예외를 catch하지 말고, 해당 예외에 대한 적절한 처리를 수행합니다.

### 성능

성능을 최적화하기 위한 몇 가지 방법입니다.

1. 메모리 사용량 최소화: 불필요한 객체를 생성하지 않고, 캐시를 효과적으로 사용합니다.
2. 코드 최적화: 반복문을 사용하여 코드를 최적화하고, 함수의 중복을 제거합니다.
3. 캐시 사용: 빈번히 호출되는 함수나 데이터에 대해 캐시를 사용하여 성능을 개선합니다.
4. 병렬 처리: 병렬 처리를 사용하여 코드의 실행 속도를 향상시킵니다.

[source: instructions/csharp-ko.instructions.md]

## 보안 (Security)
이 규칙들을 프로젝트의 .editorconfig 파일과 팀의 코드 리뷰 프로세스에 통합하여 지속적으로 고품질 코드를 유지하는 것을 목표로 해야 합니다.

| 보안 영역 | 규칙 | 설명 |
|------|------|------|
| 입력 유효성 검사 | 모든 외부 데이터 검증 (Validate all external data) | 외부(사용자, API 등)로부터 들어오는 모든 데이터는 신뢰하지 않고 항상 유효성을 검사하세요. |
| SQL 삽입 방지 | 매개변수화된 쿼리 사용 (Use parameterized queries) | 항상 매개변수화된 쿼리나 Entity Framework와 같은 ORM을 사용하여 SQL 삽입 공격을 방지하세요. |
| 민감한 데이터 보호 | 구성 관리 도구 사용 (Use configuration management tools) | 비밀번호, 연결 문자열, API 키 등은 소스 코드에 하드코딩하지 말고 Secret Manager, Azure Key Vault 등을 사용하세요. |

[source: instructions/csharp-ko.instructions.md]