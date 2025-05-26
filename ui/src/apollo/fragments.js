import gql from "graphql-tag";

const INDIVIDUAL_ENROLLMENTS = gql`
  fragment enrollments on IndividualType {
    enrollments {
      start
      end
      id
      group {
        name
        type
        parentOrg {
          name
        }
        numchild
      }
    }
  }
`;

const INDIVIDUAL_IDENTITIES = gql`
  fragment identities on IndividualType {
    identities {
      name
      source
      email
      uuid
      username
    }
  }
`;

const INDIVIDUAL_PROFILE = gql`
  fragment profile on IndividualType {
    profile {
      name
      id
      email
      isBot
      gender
      country {
        code
        name
      }
    }
  }
`;

const FULL_INDIVIDUAL = gql`
  fragment individual on IndividualType {
    mk
    isLocked
    lastReviewed
    lastModified
    ...profile
    ...identities
    ...enrollments
  }
  ${INDIVIDUAL_ENROLLMENTS}
  ${INDIVIDUAL_PROFILE}
  ${INDIVIDUAL_IDENTITIES}
`;

const CHANGELOG = gql`
  fragment changelog on ChangeLogType {
    name
    authoredBy
    createdAt
  }
`;

export {
  FULL_INDIVIDUAL,
  INDIVIDUAL_ENROLLMENTS,
  INDIVIDUAL_IDENTITIES,
  INDIVIDUAL_PROFILE,
  CHANGELOG,
};
