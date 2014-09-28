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
