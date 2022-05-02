# Change CI/CD pipeline service provider

* Status:
    * [x] proposed
    * [ ] rejected
    * [ ] accepted
    * [ ] deprecated
    * [ ] superseded by ...

## Context and Problem Statement

We want to have a CI/CD pipeline that runs for PRs and to publish packages to PYPI. Previously we used Travis CI for
this. This ADR proposes a change to a different provider.

## Decision Drivers <!-- optional -->

* Recently Travis had a security incident that potentially gave attackers access to secure assets. This is not the first
  incident of that kind
    * https://github.blog/2022-04-15-security-alert-stolen-oauth-user-tokens/
    * https://www.theregister.com/2021/09/15/travis_ci_leak/
* We were less and less happy with how to configure Travis CI
* In general Travis fell a bit out of favor in the open source community since they layed off a large part of their
  developer team

## Considered Options

* Github Actions
* Travis CI (no change)
* Gitlab

## Decision Outcome

Chosen option: "Github Actions", because

- Good integration: we currently use Github already for hosting the code repo of this project.
- actively developed, backed by big corporate $$$
- Lots of tutorials/docs available
- Very flexible (3rd party plugins are available to define actions)

### Negative Consequences <!-- optional -->

* We need to learn a new pipeline syntax.
    * However so far only me and Siebe were working on Travis actions

## Pros and Cons of the Options <!-- optional -->

### Github Actions

* Good, because well integrated with the github code repository which we use
* Good, because actively maintained/developed
* Bad, because learning new syntax is required

### Travis CI

* Good, because we know it
* Bad, because subjectively too often in the news about security incidents
* Bad, because not so actively developed anymore

### Gitlab

* Good, because all in one platform (code repo, project management, CI/CD, package repos)
* Bad, because we do not want to switch code repos at the moment
    * Yes there are ways to use a gitlab pipeline with a github repo, but why bother?

<!-- markdownlint-disable-file MD013 -->
