# Transparent Source Quality Criteria

Every important source recorded by `research-librarian` is evaluated qualitatively across four transparent dimensions (no single numerical score guarantees truth):

1. **Source Category & Authority (`source_type`)**:
   - `official_docs`: Official language/framework/protocol maintainer documentation or RFC/standard.
   - `academic_paper`: Peer-reviewed publication or academic preprint.
   - `university_resource`: University lecture notes, textbooks, or lab manuals.
   - `industry_doc`: Public standards body (NIST, OWASP, W3C, IETF) or engineering postmortem.
   - `practitioner`: Field practitioner article or Substack (valuable for case studies; verify generalizability).
   - `user_material`: Learner-supplied document or repository.
2. **Recency & Version Applicability**:
   - Record `published_date` and `access_date`. Flag undated pages or advice tied to deprecated software versions.
3. **Bias & Commercial Signals**:
   - Flag vendor sales pages, affiliate links, or product-pitch articles.
4. **Evidence Traceability**:
   - Statistical numbers and empirical claims are always attributed as the source's stated claim (`"according to [Source]..."`) with an exact URL or `[ref:...]` locator.
