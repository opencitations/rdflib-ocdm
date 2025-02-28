# Contributing to rdflib-ocdm

Thank you for considering contributing to rdflib-ocdm!

## Commit Message Convention

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages. This helps to automatically generate the changelog and determine the next semantic version number.

### Commit Message Format

Each commit message consists of a **header**, a **body**, and a **footer**:

```
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

The **header** is mandatory and the **scope** of the header is optional.

#### Type

The type must be one of the following:

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to our CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files

#### Scope

The scope should be the name of the module affected (as perceived by the person reading the changelog).

#### Subject

The subject contains a succinct description of the change:

- use the imperative, present tense: "change" not "changed" nor "changes"
- don't capitalize the first letter
- no dot (.) at the end

#### Body

The body should include the motivation for the change and contrast this with previous behavior.

#### Footer

The footer should contain any information about **Breaking Changes** and is also the place to reference GitHub issues that this commit **Closes**.

### Triggering Releases

The release process is automated and will be triggered when changes are merged to the main branch after the test workflow completes successfully.

#### Semantic Versioning

The project follows [Semantic Versioning](https://semver.org/):

- **PATCH** version (0.0.x) is incremented for backwards-compatible bug fixes
- **MINOR** version (0.x.0) is incremented for new backwards-compatible functionality
- **MAJOR** version (x.0.0) is incremented for incompatible API changes

#### How to Release Different Versions

- **Patch Release**: Fix commits (`fix:`) will trigger a patch version bump
- **Minor Release**: Feature commits (`feat:`) will trigger a minor version bump
- **Major Release**: To create a major release, include `BREAKING CHANGE:` in the commit footer, or append a `!` after the type/scope. For example:

  ```
  feat!: change API completely
  ```

  or

  ```
  feat: allow provided config object to extend other configs

  BREAKING CHANGE: `extends` key in config file is now used for extending other config files
  ```

These commit messages will trigger a major version bump when the release workflow runs.
