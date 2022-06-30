import gql from "graphql-tag";

const TOKEN_AUTH = gql`
  mutation tokenAuth($username: String!, $password: String!) {
    tokenAuth(username: $username, password: $password) {
      token
    }
  }
`;

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
        mk
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
          group {
            name
          }
          start
          end
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
        mk
        isLocked
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
          group {
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
        mk
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
          group {
            name
          }
        }
      }
    }
  }
`;

const ENROLL = gql`
  mutation enroll(
    $uuid: String!
    $group: String!
    $fromDate: DateTime
    $toDate: DateTime
    $parentOrg: String
  ) {
    enroll(
      uuid: $uuid
      group: $group
      fromDate: $fromDate
      toDate: $toDate
      parentOrg: $parentOrg
    ) {
      uuid
      individual {
        mk
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
          start
          end
          group {
            name
          }
        }
      }
    }
  }
`;

const ADD_ORGANIZATION = gql`
  mutation addOrganization($name: String!) {
    addOrganization(name: $name) {
      organization {
        name
      }
    }
  }
`;

const ADD_TEAM = gql`
  mutation addTeam(
    $teamName: String!
    $organization: String
    $parentName: String
  ) {
    addTeam(
      teamName: $teamName
      organization: $organization
      parentName: $parentName
    ) {
      team {
        name
      }
    }
  }
`;

const ADD_IDENTITY = gql`
  mutation addIdentity(
    $email: String
    $name: String
    $source: String!
    $username: String
  ) {
    addIdentity(
      email: $email
      name: $name
      source: $source
      username: $username
    ) {
      uuid
    }
  }
`;

const ADD_DOMAIN = gql`
  mutation addDomain($domain: String!, $organization: String!) {
    addDomain(domain: $domain, organization: $organization) {
      domain {
        domain
        organization {
          name
        }
      }
    }
  }
`;

const UPDATE_PROFILE = gql`
  mutation updateProfile($data: ProfileInputType!, $uuid: String) {
    updateProfile(data: $data, uuid: $uuid) {
      uuid
      individual {
        isLocked
        identities {
          uuid
          name
          email
          username
          source
        }
        profile {
          name
          email
          gender
          isBot
          country {
            code
            name
          }
        }
        enrollments {
          start
          end
          group {
            name
          }
        }
      }
    }
  }
`;

const DELETE_DOMAIN = gql`
  mutation deleteDomain($domain: String!) {
    deleteDomain(domain: $domain) {
      domain {
        domain
      }
    }
  }
`;

const WITHDRAW = gql`
  mutation withdraw(
    $uuid: String!
    $group: String!
    $fromDate: DateTime
    $toDate: DateTime
    $parentOrg: String
  ) {
    withdraw(
      uuid: $uuid
      group: $group
      fromDate: $fromDate
      toDate: $toDate
      parentOrg: $parentOrg
    ) {
      uuid
      individual {
        mk
        isLocked
        identities {
          uuid
          name
          email
          username
          source
        }
        profile {
          name
          email
          gender
          isBot
          country {
            code
            name
          }
        }
        enrollments {
          start
          end
          group {
            name
          }
        }
      }
    }
  }
`;

const DELETE_ORGANIZATION = gql`
  mutation deleteOrganization($name: String!) {
    deleteOrganization(name: $name) {
      organization {
        name
      }
    }
  }
`;

const DELETE_TEAM = gql`
  mutation deleteTeam($teamName: String!, $organization: String) {
    deleteTeam(teamName: $teamName, organization: $organization) {
      team {
        name
      }
    }
  }
`;

const UPDATE_ENROLLMENT = gql`
  mutation updateEnrollment(
    $fromDate: DateTime!
    $newFromDate: DateTime
    $newToDate: DateTime
    $group: String!
    $toDate: DateTime!
    $uuid: String!
    $parentOrg: String
  ) {
    updateEnrollment(
      fromDate: $fromDate
      newFromDate: $newFromDate
      newToDate: $newToDate
      group: $group
      toDate: $toDate
      uuid: $uuid
      parentOrg: $parentOrg
    ) {
      uuid
      individual {
        isLocked
        identities {
          uuid
          name
          email
          username
          source
        }
        profile {
          name
          email
          gender
          isBot
          country {
            code
            name
          }
        }
        enrollments {
          start
          end
          group {
            name
          }
        }
      }
    }
  }
`;

const tokenAuth = (apollo, username, password) => {
  const response = apollo.mutate({
    mutation: TOKEN_AUTH,
    variables: {
      username: username,
      password: password
    }
  });
  return response;
};

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

const enroll = (apollo, uuid, group, fromDate, toDate, parentOrg) => {
  let response = apollo.mutate({
    mutation: ENROLL,
    variables: {
      uuid: uuid,
      group: group,
      fromDate: fromDate,
      toDate: toDate,
      parentOrg: parentOrg
    }
  });
  return response;
};

const addIdentity = (apollo, email, name, source, username) => {
  let response = apollo.mutate({
    mutation: ADD_IDENTITY,
    variables: {
      email: email,
      name: name,
      source: source,
      username: username
    }
  });
  return response;
};

const updateProfile = (apollo, data, uuid) => {
  let response = apollo.mutate({
    mutation: UPDATE_PROFILE,
    variables: {
      data: data,
      uuid: uuid
    }
  });
  return response;
};

const addOrganization = (apollo, name) => {
  let response = apollo.mutate({
    mutation: ADD_ORGANIZATION,
    variables: {
      name: name
    }
  });
  return response;
};

const addTeam = (apollo, teamName, organization, parentName) => {
  let response = apollo.mutate({
    mutation: ADD_TEAM,
    variables: {
      teamName: teamName,
      organization: organization,
      parentName: parentName
    }
  });
  return response;
};

const addDomain = (apollo, domain, organization) => {
  let response = apollo.mutate({
    mutation: ADD_DOMAIN,
    variables: {
      domain: domain,
      organization: organization
    }
  });
  return response;
};

const deleteDomain = (apollo, domain) => {
  let response = apollo.mutate({
    mutation: DELETE_DOMAIN,
    variables: { domain: domain }
  });
  return response;
};

const withdraw = (apollo, uuid, group, fromDate, toDate, parentOrg) => {
  let response = apollo.mutate({
    mutation: WITHDRAW,
    variables: {
      uuid: uuid,
      group: group,
      fromDate: fromDate,
      toDate: toDate,
      parentOrg: parentOrg
    }
  });
  return response;
};

const deleteOrganization = (apollo, name) => {
  let response = apollo.mutate({
    mutation: DELETE_ORGANIZATION,
    variables: { name: name }
  });
  return response;
};

const deleteTeam = (apollo, teamName, organization) => {
  let response = apollo.mutate({
    mutation: DELETE_TEAM,
    variables: {
      teamName: teamName,
      organization: organization
    }
  });
  return response;
};

const updateEnrollment = (apollo, data) => {
  let response = apollo.mutate({
    mutation: UPDATE_ENROLLMENT,
    variables: {
      fromDate: data.fromDate,
      newFromDate: data.newFromDate,
      newToDate: data.newToDate,
      group: data.group,
      toDate: data.toDate,
      uuid: data.uuid,
      parentOrg: data.parentOrg
    }
  });
  return response;
};

export {
  tokenAuth,
  lockIndividual,
  unlockIndividual,
  deleteIdentity,
  merge,
  unmerge,
  moveIdentity,
  enroll,
  addOrganization,
  deleteOrganization,
  addDomain,
  deleteDomain,
  addTeam,
  deleteTeam,
  addIdentity,
  updateProfile,
  withdraw,
  updateEnrollment
};
