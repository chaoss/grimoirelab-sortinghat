import gql from "graphql-tag";

const INDIVIDUAL_ENROLLMENTS = gql`
  fragment enrollments on IndividualType {
    enrollments {
      start
      end
      group {
        name
        type
        parentOrg {
          name
        }
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
    ...profile
    ...identities
    ...enrollments
  }
  ${INDIVIDUAL_ENROLLMENTS}
  ${INDIVIDUAL_PROFILE}
  ${INDIVIDUAL_IDENTITIES}
`;

export {
  FULL_INDIVIDUAL,
  INDIVIDUAL_ENROLLMENTS,
  INDIVIDUAL_IDENTITIES,
  INDIVIDUAL_PROFILE,
};
