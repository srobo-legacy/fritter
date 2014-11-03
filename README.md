# fritter

[![Build Status](https://travis-ci.org/PeterJCLaw/fritter.svg)](https://travis-ci.org/PeterJCLaw/fritter)

A service which creates mailshots from templated emails submitted via Gerrit

## The problem

When sending emails to large numbers of people, it is desirable that:
* The email's content is reviewed before sending, to ensure that it
  conveys the right information and is free from errors.
* Anyone can easily send an email once the review is complete, without
  needing to actually know all the email address of the recipients.

## How it works

When a gerrit patchset is merged into the target repository it is inspected
to see if it contains any new template files. Any templates found are
inspected to see who to send them to, as determined via group mappings
within an LDAP database, and then queued for sending.

## Configuration
See `config.ini` for the defaults and explanations. All the various scripts
also load a `local.ini` which can override any of the values.

Note that due to the way that srusers works, its LDAP connection unfortunately
needs to be configured separate via config files within its own repo.

## Template Previewing
Most users will likely want to preview a template without worrying about
the rest of the system. This is supported as follows:

    ./preview REPO REVISION_HASH

When given the path to a repo and a revision, this will show a preview of
all the files in that commit which would be picked up by fritter for sending.
Since this uses the same logic as the core service it will generate the
same result as submitting the revision to a Gerrit instance being monitored
(as long as the configurations are similar).

Users may also be interested in the similar script within the libfritter repo.

## Development
To ease development without needing to submit things into Gerrit, there is
a `./dev` script which can be given a file containing a single Gerrit event.
This will trigger the system as though the event had come from Gerrit,
including submitting back the preview information. As a result, a Gerrit
instance is still needed to use this script.

Tests can be run with `./run-local-tests`, which will just run the tests
which belong to fritter. Running `nosetests` should also work, though this
will find all the tests in submodules as well.

## Deployment
There are two executables which need to be set up:
* `fritter-service` should be run as a service. This connects to Gerrit
  to listen for changes and emit previews. It also sets up the emails for
  sending when the templates are submitted
* `fritter-cron` should run occasionally as a cron job. This queries the
  local sqlite database for emails to send and sends any that need sending.
