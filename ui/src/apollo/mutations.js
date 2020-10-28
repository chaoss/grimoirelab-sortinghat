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
          name
          source
          email
          uuid
          username
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

const UNMERGE = gql`
  mutation unmerge($uuids: [String!]) {
    unmergeIdentities(uuids: $uuids) {
      uuids
      individuals {
        profile {
          name
          id
          isBot
        }
        identities {
          name
          source
          email
          uuid
          username
        }
        enrollments {
          start
          end
          organization {
            name
          }
        }
      }
    }
  }
`;

const MOVE_IDENTITY = gql`
  mutation moveIdentity($fromUuid: String!, $toUuid: String!) {
    moveIdentity(fromUuid: $fromUuid, toUuid: $toUuid) {
      uuid
      individual {
        isLocked
        identities {
          name
          source
          email
          uuid
          username
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

const unmerge = (apollo, uuids) => {
  let response = apollo.mutate({
    mutation: UNMERGE,
    variables: {
      uuids: uuids
    }
  });
  return response;
};

const moveIdentity = (apollo, fromUuid, toUuid) => {
  let response = apollo.mutate({
    mutation: MOVE_IDENTITY,
    variables: {
      fromUuid: fromUuid,
      toUuid: toUuid
    }
  });
  return response;
};

export {
  lockIndividual,
  unlockIndividual,
  deleteIdentity,
  merge,
  unmerge,
  moveIdentity
};
