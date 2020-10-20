import gql from "graphql-tag";

const LOCK_INDIVIDUAL = gql`
  mutation LockIndividual($uuid: String!) {
    lock(uuid: $uuid) {
      uuid
      individual {
        isLocked
      }
    }
  }
`;

const UNLOCK_INDIVIDUAL = gql`
  mutation UnlockIndividual($uuid: String!) {
    unlock(uuid: $uuid) {
      uuid
      individual {
        isLocked
      }
    }
  }
`;

const DELETE_IDENTITY = gql`
  mutation DeleteIdentity($uuid: String!) {
    deleteIdentity(uuid: $uuid) {
      uuid
    }
  }
`;

const MERGE = gql`
  mutation Merge($fromUuids: [String!], $toUuid: String!) {
    merge(fromUuids: $fromUuids, toUuid: $toUuid) {
      uuid
      individual {
        isLocked
        identities {
          source
        }
        profile {
          name
          id
        }
        enrollments {
          organization {
            name
          }
        }
      }
    }
  }
`;

const lockIndividual = (apollo, uuid) => {
  let response = apollo.mutate({
    mutation: LOCK_INDIVIDUAL,
    variables: {
      uuid: uuid
    }
  });
  return response;
};

const unlockIndividual = (apollo, uuid) => {
  let response = apollo.mutate({
    mutation: UNLOCK_INDIVIDUAL,
    variables: {
      uuid: uuid
    }
  });
  return response;
};

const deleteIdentity = (apollo, uuid) => {
  let response = apollo.mutate({
    mutation: DELETE_IDENTITY,
    variables: {
      uuid: uuid
    }
  });
  return response;
};

const merge = (apollo, fromUuids, toUuid) => {
  let response = apollo.mutate({
    mutation: MERGE,
    variables: {
      fromUuids: fromUuids,
      toUuid: toUuid
    }
  });
  return response;
};

export { lockIndividual, unlockIndividual, deleteIdentity, merge };
