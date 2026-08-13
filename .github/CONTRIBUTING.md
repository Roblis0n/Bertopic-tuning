# Contributing to BERTopic Tuning

Thank you for improving an auditable, semantic-first BERTopic workflow. This
repository intentionally separates algorithmic diagnostics from human
interpretation: diagnostics prioritize material for review; they do not decide
topic meanings, labels, merges, splits, or model promotion.

## Before opening an issue or pull request

1. Read the relevant route guidance for `network-short`, `long-document`, or
   `mixed` corpora and select the assurance level: `exploratory`, `research`,
   or `publication_release`.
2. Search existing issues and pull requests.
3. Run the full offline suite from the repository root:

   ```text
   python -X utf8 -B -m unittest discover -s scripts/tests -v
   ```

4. Use a minimal, privacy-safe fixture. Never commit raw participant text,
   confidential documents, credentials, or proprietary corpus material.

## Contribution standards

- Keep a change focused and preserve existing artifacts unless the change
  explicitly updates their contract.
- Keep commands portable across PowerShell, Command Prompt, and POSIX shells.
- Use UTF-8 for text resources and preserve the line-ending rules in
  `.gitattributes`.
- Add or update `unittest` coverage for behavioral changes; run the whole
  suite, not only the test you changed.
- Explain whether the change affects structure, representation, taxonomy, or
  governance. Representation-only changes must preserve assignment and topic
  identity fingerprints.
- For methodology changes, state the corpus route, assurance level, evidence
  considered, and limitations. Do not introduce universal parameter values,
  reviewer counts, or promotion claims without target-corpus evidence.

## Pull request checklist

- [ ] I ran the full test command above with UTF-8 enabled.
- [ ] I documented the corpus route and assurance level affected, or explained
      why the change is corpus-independent.
- [ ] I included a minimal privacy-safe fixture when reproducing a failure.
- [ ] I updated documentation, examples, or artifacts when the user-facing
      contract changed.
- [ ] I did not add sensitive corpus material or secrets.
