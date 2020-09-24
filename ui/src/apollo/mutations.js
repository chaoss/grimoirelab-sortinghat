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

export { lockIndividual, unlockIndividual };
