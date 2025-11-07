# Knowledge Graph Best Practices

## KG schema best practices
**prompt**  
what are best practices for designing a knowledge graph schema

**response**  
Start from use-cases, not data. Write competency questions. Model only what you need to answer.

### Core principles
- Prefer simple, stable shapes. Add complexity only when forced.
- One concept = one class. One meaning per property.
- Use event-centric modeling for anything that changes over time.
- Choose global, immutable identifiers. Never reuse IDs.

### Identity and keys
- Mint HTTP-resolvable IRIs. Keep a single canonical IRI per entity.
- Record external IDs as properties with datatype and issuer.
- Model sameness with `owl:sameAs` sparingly; prefer `skos:exactMatch` across catalogs.

### Vocabulary strategy
- Reuse well-known ontologies first: Schema.org, SKOS, PROV-O, Dublin Core, GeoSPARQL.
- Extend with a thin domain namespace. Avoid deep class hierarchies.
- Document each class/property with label, comment, domain, range, examples.

### Relations and shapes
- Model n-ary facts as nodes (events/agreements/measurements) with roles and time.
- Encode time using `prov:startedAtTime` / `endedAtTime` or `time:TemporalEntity`.
- Represent uncertainty with qualifiers (probability, source, method).
- Use SHACL or ShEx for validation. Ship shape files with the schema.

### Provenance and lineage
- Attach source, method, and timestamp to every assertion node or named graph.
- Use named graphs to separate ingestion, curation, and inferred statements.
- Track transformations as PROV activities to make pipelines auditable.

### Constraints and semantics
- Keep open-world in mind. Avoid `owl:FunctionalProperty` unless certain.
- Prefer competency-question tests over OWL “magic.” Reason only where it pays off.
- Encode cardinalities and required fields in SHACL, not prose.

### Versioning and evolution
- Semantic version the ontology. Never delete; deprecate with `owl:deprecated true`.
- Add new properties instead of changing ranges. Provide migration notes.
- Freeze IRIs. Use new IRIs for breaking changes.

### Performance and layout
- Design for query paths you will run. Benchmark SPARQL early.
- Avoid hyperconnected supernodes. Introduce intermediary nodes to cap degree.
- Index common join keys. Partition by named graph, time, or domain.
- Denormalize selectively into materialized views for hot queries.

### Interop and modeling choices
- Use SKOS for taxonomies and tags; keep it separate from OWL classes.
- Prefer `schema:Organization` and role nodes for people-in-orgs over direct edges.
- Geospatial: use GeoSPARQL geometries; store WKT and CRS.
- Text: keep literals with language tags; maintain normalized and raw variants.

### Governance
- Run schema proposals through design reviews tied to competency questions.
- Maintain a changelog, examples, and a minimal cookbook of patterns.
- Lint the KG in CI: SHACL validation, IRI style, domain/range checks, CQ tests.

### Security and PII
- Isolate sensitive triples in separate graphs. Apply access control at graph level.
- Minimize PII. Use hashing or tokens for quasi-identifiers.

### Testing and quality
- Gold-standard fixtures for each pattern.
- Coverage: % of triples with provenance, time, and source.
- Drift alerts on shape violations and degree explosions.

### Anti-patterns to avoid
- Entity soup with unlabeled IRIs.
- Overusing `owl:sameAs` for loose matches.
- Modeling every column as a property 1:1.
- Encoding business rules only in documentation.
- Time as literals on edges without proper event nodes.

### Minimal pattern examples
- **Role pattern**: `:Employment a :Role ; :agent :Alice ; :at :ACME ; :role "Engineer" ; prov:startedAtTime "2023-01-01"^^xsd:date .`
- **Observation pattern**: `:Obs123 a :Measurement ; :of :CPU_Usage ; :value "0.82"^^xsd:decimal ; :unit "ratio" ; prov:generatedAtTime ... ; :source :Prometheus .`

### Startup checklist
1. Write 10–20 competency questions.
2. Sketch classes, roles, events. Keep ≤30 core terms.
3. Pick reused vocabularies and define gaps.
4. Author SHACL shapes and example data.
5. Run CQ queries on a toy graph. Iterate.
6. Add provenance and time everywhere.
7. Freeze IRIs. Publish docs and CI checks.
8. Load first real slice. Benchmark. Adjust indexes and shapes.

If you share a domain and two sample competency questions, I will draft a minimal schema and SHACL to start.

---

## Define competency questions
**prompt**  
What is a competency question?

**response**  
A competency question is a testable, natural-language question that defines what the knowledge graph must be able to answer. It expresses scope and requirements before schema design.

Examples:  
- “Which suppliers provide components for product X?”  
- “What research papers cite dataset Y?”  
- “Who held the role of CEO at company Z in 2022?”  

Each competency question anchors:  
1. **Required entities** (supplier, product, dataset, person, company).  
2. **Relations** (supplies, cites, heldRole).  
3. **Constraints** (time, provenance, version).  

Design steps:  
1. Collect 10–20 such questions from domain users.  
2. Model only the concepts needed to answer them.  
3. Validate the schema by checking that each question can be answered with one SPARQL query.  

They function as acceptance tests for ontology and data coverage.

---

## Provide competency questions
**prompt**  
This is a starting set of competency questions

**response**  
Understood. Paste or list them. I will:  
1. Group them by domain focus.  
2. Identify required entities, relations, and event types.  
3. Highlight missing concepts or potential modeling conflicts.  
4. Suggest schema primitives and SHACL patterns to cover them.

---

## Analyze listed questions
**prompt**  
- What are the “domain model” validation rules for “product name”?
- Can validation rules for “domain model” be customized by a customer?
    - does the answer depend on user role, product tier, organization rules
- Show me the user guides and other customer support knowledge we publish for our customers to understand and use validation rules for “domain model”
- I need to modify validation rules for “domain model”. Where do I make these changes and do we have design or implementation notes for such changes?
- Tell me about the UX design for customizing validation rules.
- Are there any current tasks or backlogged tasks related to validation rules?
- Explain the solution architecture for “product name”

**response**  
You can cover all seven with a small, event-centric schema. Below is the minimal map.

### Clusters → concepts
- **Validation rules & scope**: `ValidationRule`, `DomainModel`, `Product`, `Field` (e.g., “product name”), `Severity`, `Expression`/`Checker`.
- **Customization & governance**: `CustomerOrg`, `User`, `UserRole`, `ProductTier`, `OrgPolicy`, `RuleCustomization` (event), `Entitlement`.
- **Docs/knowledge**: `KnowledgeArticle` (guides), `DocType`, `Publication` (event), `URL`.
- **Change points**: `DesignNote`, `ImplementationArtifact` (repo path, service), `RuleChange` (event), `SourceControlRef`.
- **UX**: `UXAsset` (flows, wireframes), `UXDecision`.
- **Work tracking**: `WorkItem` (task/epic), `Status`, `Backlog`, `Tracker`.
- **Architecture**: `SystemComponent`, `Interface`, `ArchitectureView`, `Dependency`.

### Core relations
- `ValidationRule appliesTo Field`
- `ValidationRule scopedBy DomainModel`
- `ValidationRule documentedIn KnowledgeArticle`
- `RuleCustomization customizes ValidationRule ; for CustomerOrg`
- `Entitlement permits Action for {UserRole | ProductTier | CustomerOrg}`
- `RuleChange modifies ValidationRule ; implementedIn ImplementationArtifact ; describedBy DesignNote`
- `WorkItem about {ValidationRule|Customization}`
- `SystemComponent partOf Product ; documentedIn ArchitectureView`

### Event types (for time/version)
- `RuleEvaluation` (runtime), `RuleCustomization` (policy change), `RuleChange` (code/config change), `Publication`, `WorkItemStateChange`, `Deployment`.

### CQ coverage → what to model/run
1) **“What are the ‘domain model’ validation rules for ‘product name’?”**  
   Path: `DomainModel → ValidationRule → Field("product name")`. Include `severity`, `message`, `expression`, `version`, `effectiveTime`.

2) **“Can validation rules be customized by a customer? Does it depend on role, tier, org rules?”**  
   Path: `ValidationRule ← RuleCustomization → CustomerOrg` plus `Entitlement` over `UserRole`, `ProductTier`, `OrgPolicy`. Add resolution order.

3) **“Show user guides and other support knowledge…”**  
   Path: `ValidationRule → documentedIn → KnowledgeArticle` filtered by `DocType in {UserGuide, FAQ}` and `Publication.status = Published`.

4) **“I need to modify validation rules… Where to change and do we have notes?”**  
   Path: `ValidationRule → implementedIn (repo/service/file)` and `describedBy → DesignNote`. Include `Owner` and `ChangeProcess`.

5) **“Tell me about the UX design for customizing validation rules.”**  
   Path: `Customization flow → UXAsset (flows/specs)` and `UXDecision`.

6) **“Any current or backlogged tasks related to validation rules?”**  
   Path: `WorkItem about ValidationRule` with `Status ∈ {Open, InProgress, Backlog}`.

7) **“Explain the solution architecture for ‘product name’.”**  
   Path: `Product → SystemComponent → Interface/Dependency → ArchitectureView`.

### SHACL skeletons (minimal)

```turtle
:ValidationRuleShape a sh:NodeShape ;
  sh:targetClass :ValidationRule ;
  sh:property [
    sh:path :appliesTo ; sh:class :Field ; sh:minCount 1
  ],[
    sh:path :scopedBy ; sh:class :DomainModel ; sh:minCount 1
  ],[
    sh:path :severity ; sh:in ("error" "warn" "info")
  ],[
    sh:path :expression ; sh:datatype xsd:string ; sh:minCount 1
  ],[
    sh:path :effectiveFrom ; sh:datatype xsd:dateTime
  ] .
```

```turtle
:RuleCustomizationShape a sh:NodeShape ;
  sh:targetClass :RuleCustomization ;
  sh:property [
    sh:path :customizes ; sh:class :ValidationRule ; sh:minCount 1
  ],[
    sh:path :for ; sh:class :CustomerOrg ; sh:minCount 1
  ],[
    sh:path :condition ; sh:class :EntitlementCondition ; sh:minCount 1
  ],[
    sh:path :change ; sh:class :RuleDelta ; sh:minCount 1
  ] .
```

```turtle
:KnowledgeArticleShape a sh:NodeShape ;
  sh:targetClass :KnowledgeArticle ;
  sh:property [
    sh:path :docType ; sh:in ("UserGuide" "HowTo" "FAQ" "APIRef")
  ],[
    sh:path :url ; sh:datatype xsd:anyURI ; sh:minCount 1
  ],[
    sh:path :covers ; sh:class :ValidationRule
  ],[
    sh:path :publishedAt ; sh:datatype xsd:dateTime
  ] .
```

```turtle
:WorkItemShape a sh:NodeShape ;
  sh:targetClass :WorkItem ;
  sh:property [
    sh:path :about ; sh:class :ValidationRule ; sh:minCount 1
  ],[
    sh:path :status ; sh:in ("Backlog" "Open" "InProgress" "Blocked" "Done")
  ],[
    sh:path :tracker ; sh:datatype xsd:string
  ] .
```

```turtle
:SystemComponentShape a sh:NodeShape ;
  sh:targetClass :SystemComponent ;
  sh:property [
    sh:path :partOf ; sh:class :Product ; sh:minCount 1
  ],[
    sh:path :dependsOn ; sh:class :SystemComponent
  ],[
    sh:path :documentedIn ; sh:class :ArchitectureView
  ] .
```

### Example triples (pattern)
```turtle
:Rule_PName_NotEmpty a :ValidationRule ;
  :appliesTo :Field_ProductName ;
  :scopedBy :DomainModel_Main ;
  :severity "error" ;
  :expression "len(value)>0" ;
  :documentedIn :KA_UG_CustomizingRules .

:Cus_ABC_PNameOverride a :RuleCustomization ;
  :customizes :Rule_PName_NotEmpty ;
  :for :CustomerOrg_ABC ;
  :condition [ a :EntitlementCondition ;
               :userRole "Admin" ; :productTier "Enterprise" ] ;
  :change [ a :RuleDelta ; :severity "warn" ] .

:RuleChange_123 a :RuleChange ;
  :modifies :Rule_PName_NotEmpty ;
  :implementedIn [ a :ImplementationArtifact ;
                   :service "validation-svc" ;
                   :repoPath "git://.../rules/product_name.yaml" ] ;
  :describedBy :DesignNote_456 .
```

### SPARQL skeletons per CQ
- Rules for field:
```sparql
SELECT ?rule ?severity ?expr ?version WHERE {
  ?rule a :ValidationRule ; :appliesTo :Field_ProductName ; :scopedBy :DomainModel_Main ;
        :severity ?severity ; :expression ?expr .
  OPTIONAL { ?rule :version ?version }
}
```
- Customization feasibility and dependencies:
```sparql
ASK { ?c a :RuleCustomization ; :customizes ?rule ; :for ?org . }
SELECT ?rule ?org ?role ?tier WHERE {
  ?c a :RuleCustomization ; :customizes ?rule ; :for ?org ;
     :condition [ :userRole ?role ; :productTier ?tier ] .
}
```
- Docs:
```sparql
SELECT ?title ?url WHERE {
  ?ka a :KnowledgeArticle ; :docType "UserGuide" ;
      :covers ?rule ; :url ?url ; rdfs:label ?title .
}
```
- Where to change:
```sparql
SELECT ?service ?repoPath ?designNote WHERE {
  ?chg a :RuleChange ; :modifies ?rule ;
       :implementedIn [ :service ?service ; :repoPath ?repoPath ] ;
       :describedBy ?designNote .
}
```
- UX:
```sparql
SELECT ?asset ?type WHERE {
  ?asset a :UXAsset ; :covers :RuleCustomization ; :assetType ?type .
}
```
- Tasks/backlog:
```sparql
SELECT ?item ?status ?tracker WHERE {
  ?item a :WorkItem ; :about ?rule ; :status ?status ; :tracker ?tracker .
  FILTER (?status IN ("Backlog","Open","InProgress"))
}
```
- Architecture:
```sparql
CONSTRUCT { ?c :dependsOn ?d } WHERE {
  :Product_X :hasComponent ?c . OPTIONAL { ?c :dependsOn ?d }
}
```

### Resolution rules you must encode
- **Policy order**: `OrgPolicy > ProductTier > UserRole` or another explicit precedence. Store as integers for deterministic evaluation.
- **Tenant isolation**: keep `RuleCustomization` in per-tenant named graphs.
- **Versioning**: rules are immutable by IRI; changes create new IRIs with `prov:wasRevisionOf`.

### Gaps to clarify
- Exact set of `Field`s in the “domain model.”  
- Runtime engine for `expression` (DSL vs code).  
- Entitlement precedence and default behavior.  
- Trackers in use (Jira, Linear, GitHub).  
- Canonical sources for docs and design notes.

If you confirm policy precedence and the expression engine, I’ll output a concrete ontology file and SHACL pack you can load on day one.

---

## Simplify schema model
**prompt**  
This is unnecessarily complicated. We do not need such fine-grained entities. Use abstraction and simplification. Focus first on nodes and relationships.

**response**  
Here’s a simplified, abstraction-first schema. Ten node types, twelve relationships. No micro-entities.

### Node types
`Product`, `Model`, `Field`, `Rule`, `Customer`, `Override`, `Doc`, `Artifact`, `UX`, `Task`, `Component`

### Relationships
- `Product HAS_MODEL Model`
- `Model HAS_FIELD Field`
- `Rule APPLIES_TO Field`
- `Rule SCOPED_BY Model`
- `Rule DOCUMENTED_BY Doc`
- `Rule IMPLEMENTED_IN Artifact`
- `Rule REFERENCED_BY Task`  *(work related to a rule)*
- `Rule DESCRIBED_BY UX`  *(UX for customizing/using rules)*
- `Rule OVERRIDDEN_BY Override`
- `Override FOR_CUSTOMER Customer`
- `Product HAS_COMPONENT Component`
- `Component DEPENDS_ON Component`
- `Component DOCUMENTED_BY Doc`

### Minimal attributes
- `Rule:{id,name,severity,message,expression,version}`
- `Override:{id,change(severity|message|expr),role?,tier?,orgPolicy?,effectiveFrom?,effectiveTo?}`
- `Doc:{id,type(UserGuide|HowTo|APIRef|Design),url,title,status}`
- `Artifact:{id,service,repoPath}`
- `Task:{id,status(Backlog|Open|InProgress|Blocked|Done),tracker,url}`
- Others: `{id,name}`

### Why this covers your CQs
1) Rules for “product name” in “domain model”  
   `Model–HAS_FIELD→Field("product name") ←APPLIES_TO–Rule`  
2) Customizable by customer; depends on role/tier/org rules  
   `Rule–OVERRIDDEN_BY→Override–FOR_CUSTOMER→Customer` with optional `role/tier/orgPolicy` attributes.  
3) Guides/support knowledge  
   `Rule–DOCUMENTED_BY→Doc(type in {UserGuide,HowTo,FAQ})`  
4) Where to change; notes  
   `Rule–IMPLEMENTED_IN→Artifact` and `Rule–DOCUMENTED_BY→Doc(type="Design")`  
5) UX design  
   `Rule–DESCRIBED_BY→UX`  
6) Current/backlogged tasks  
   `Task–REFERENCES→Rule` (or `Rule REFERENCED_BY Task`) with `status`  
7) Solution architecture  
   `Product–HAS_COMPONENT→Component–DEPENDS_ON→Component`, `Component–DOCUMENTED_BY→Doc`

### Qualified relations rule
Only introduce `Override` when you need attributes on a relation (role/tier/effective dates). Everything else stays as direct edges.

### Example edge list (CSV style)
```
Model_Main,HAS_FIELD,Field_ProductName
Rule_PName_NotEmpty,APPLIES_TO,Field_ProductName
Rule_PName_NotEmpty,SCOPED_BY,Model_Main
Rule_PName_NotEmpty,DOCUMENTED_BY,Doc_UserGuide_CustomRules
Rule_PName_NotEmpty,IMPLEMENTED_IN,Art_validation_svc_rules_yaml
Rule_PName_NotEmpty,OVERRIDDEN_BY,Ov_ABC_PName_Warn
Ov_ABC_PName_Warn,FOR_CUSTOMER,Cust_ABC
Product_X,HAS_MODEL,Model_Main
Product_X,HAS_COMPONENT,Comp_ValidationSvc
Comp_ValidationSvc,DEPENDS_ON,Comp_RulesRepo
Task_123,REFERENCES,Rule_PName_NotEmpty
Rule_PName_NotEmpty,DESCRIBED_BY,UX_CustomizationFlow
```

### Query skeletons
- Rules for field in model:
```
MATCH (m:Model {id:$model})-[:HAS_FIELD]->(f:Field {id:$field})
MATCH (r:Rule)-[:APPLIES_TO]->(f) AND (r)-[:SCOPED_BY]->(m)
RETURN r
```
- Is customization allowed and on what bases:
```
MATCH (r:Rule {id:$rule})-[:OVERRIDDEN_BY]->(o:Override)-[:FOR_CUSTOMER]->(c:Customer {id:$cust})
RETURN o.role,o.tier,o.orgPolicy,o.effectiveFrom,o.effectiveTo
```
- Docs for rules:
```
MATCH (r:Rule {id:$rule})-[:DOCUMENTED_BY]->(d:Doc)
WHERE d.type IN ["UserGuide","HowTo","FAQ"]
RETURN d
```
- Where to change + design notes:
```
MATCH (r:Rule {id:$rule})-[:IMPLEMENTED_IN]->(a:Artifact)
OPTIONAL MATCH (r)-[:DOCUMENTED_BY]->(d:Doc {type:"Design"})
RETURN a.repoPath,a.service,d.url
```
- Tasks:
```
MATCH (t:Task)-[:REFERENCES]->(:Rule {id:$rule})
WHERE t.status IN ["Backlog","Open","InProgress"]
RETURN t
```
- Architecture:
```
MATCH (:Product {id:$product})-[:HAS_COMPONENT]->(c:Component)
OPTIONAL MATCH (c)-[:DEPENDS_ON]->(d:Component)
RETURN c,d
```

### Build order
1) Load nodes for `Product, Model, Field, Rule`.  
2) Wire the six core edges: `HAS_MODEL`, `HAS_FIELD`, `APPLIES_TO`, `SCOPED_BY`, `DOCUMENTED_BY`, `IMPLEMENTED_IN`.  
3) Add `Override` only where needed.  
4) Add `Task`, `UX`, `Component` incrementally.

If you want, I’ll emit a compact Neo4j `:auto USING PERIODIC COMMIT` loader with these types and edges.
