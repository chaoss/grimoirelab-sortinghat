import gql from "graphql-tag";
import { FULL_INDIVIDUAL } from "./fragments";

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
        ...individual
      }
    }
  }
  ${FULL_INDIVIDUAL}
`;

const UNMERGE = gql`
  mutation unmerge($uuids: [String!]) {
    unmergeIdentities(uuids: $uuids) {
      uuids
      individuals {
        ...individual
      }
    }
  }
  ${FULL_INDIVIDUAL}
`;

const MOVE_IDENTITY = gql`
  mutation moveIdentity($fromUuid: String!, $toUuid: String!) {
    moveIdentity(fromUuid: $fromUuid, toUuid: $toUuid) {
      uuid
      individual {
        ...individual
      }
    }
  }
  ${FULL_INDIVIDUAL}
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
        ...individual
      }
    }
  }
  ${FULL_INDIVIDUAL}
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
  mutation addDomain(
    $domain: String!
    $isTopDomain: Boolean
    $organization: String!
  ) {
    addDomain(
      domain: $domain
      isTopDomain: $isTopDomain
      organization: $organization
    ) {
      domain {
        domain
        isTopDomain
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
        ...individual
      }
    }
  }
  ${FULL_INDIVIDUAL}
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
        ...individual
      }
    }
  }
  ${FULL_INDIVIDUAL}
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
        ...individual
      }
    }
  }
  ${FULL_INDIVIDUAL}
`;

const AFFILIATE = gql`
  mutation affiliate($uuids: [String]) {
    affiliate(uuids: $uuids) {
      jobId
    }
  }
`;

const GENDERIZE = gql`
  mutation genderize(
    $uuids: [String]
    $exclude: Boolean
    $noStrictMatching: Boolean
  ) {
    genderize(
      uuids: $uuids
      exclude: $exclude
      noStrictMatching: $noStrictMatching
    ) {
      jobId
    }
  }
`;

const UNIFY = gql`
  mutation unify($criteria: [String], $exclude: Boolean) {
    unify(criteria: $criteria, exclude: $exclude) {
      jobId
    }
  }
`;

const MANAGE_MERGE_RECOMMENDATION = gql`
  mutation manageMergeRecommendation($recommendationId: Int!, $apply: Boolean) {
    manageMergeRecommendation(
      recommendationId: $recommendationId
      apply: $apply
    ) {
      applied
    }
  }
`;

const RECOMMEND_MATCHES = gql`
  mutation recommendMatches($criteria: [String], $exclude: Boolean) {
    recommendMatches(criteria: $criteria, exclude: $exclude) {
      jobId
    }
  }
`;

const tokenAuth = (apollo, username, password) => {
  const response = apollo.mutate({
    mutation: TOKEN_AUTH,
    variables: {
      username: username,
      password: password,
    },
  });
  return response;
};

const lockIndividual = (apollo, uuid) => {
  let response = apollo.mutate({
    mutation: LOCK_INDIVIDUAL,
    variables: {
      uuid: uuid,
    },
  });
  return response;
};

const unlockIndividual = (apollo, uuid) => {
  let response = apollo.mutate({
    mutation: UNLOCK_INDIVIDUAL,
    variables: {
      uuid: uuid,
    },
  });
  return response;
};

const deleteIdentity = (apollo, uuid) => {
  let response = apollo.mutate({
    mutation: DELETE_IDENTITY,
    variables: {
      uuid: uuid,
    },
  });
  return response;
};

const merge = (apollo, fromUuids, toUuid) => {
  let response = apollo.mutate({
    mutation: MERGE,
    variables: {
      fromUuids: fromUuids,
      toUuid: toUuid,
    },
  });
  return response;
};

const unmerge = (apollo, uuids) => {
  let response = apollo.mutate({
    mutation: UNMERGE,
    variables: {
      uuids: uuids,
    },
  });
  return response;
};

const moveIdentity = (apollo, fromUuid, toUuid) => {
  let response = apollo.mutate({
    mutation: MOVE_IDENTITY,
    variables: {
      fromUuid: fromUuid,
      toUuid: toUuid,
    },
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
      parentOrg: parentOrg,
    },
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
      username: username,
    },
  });
  return response;
};

const updateProfile = (apollo, data, uuid) => {
  let response = apollo.mutate({
    mutation: UPDATE_PROFILE,
    variables: {
      data: data,
      uuid: uuid,
    },
  });
  return response;
};

const addOrganization = (apollo, name) => {
  let response = apollo.mutate({
    mutation: ADD_ORGANIZATION,
    variables: {
      name: name,
    },
  });
  return response;
};

const addTeam = (apollo, teamName, organization, parentName) => {
  let response = apollo.mutate({
    mutation: ADD_TEAM,
    variables: {
      teamName: teamName,
      organization: organization,
      parentName: parentName,
    },
  });
  return response;
};

const addDomain = (apollo, domain, isTopDomain, organization) => {
  let response = apollo.mutate({
    mutation: ADD_DOMAIN,
    variables: {
      domain: domain,
      isTopDomain: isTopDomain,
      organization: organization,
    },
  });
  return response;
};

const deleteDomain = (apollo, domain) => {
  let response = apollo.mutate({
    mutation: DELETE_DOMAIN,
    variables: { domain: domain },
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
      parentOrg: parentOrg,
    },
  });
  return response;
};

const deleteOrganization = (apollo, name) => {
  let response = apollo.mutate({
    mutation: DELETE_ORGANIZATION,
    variables: { name: name },
  });
  return response;
};

const deleteTeam = (apollo, teamName, organization) => {
  let response = apollo.mutate({
    mutation: DELETE_TEAM,
    variables: {
      teamName: teamName,
      organization: organization,
    },
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
      parentOrg: data.parentOrg,
    },
  });
  return response;
};

const affiliate = (apollo, uuids) => {
  return apollo.mutate({
    mutation: AFFILIATE,
    variables: {
      uuids: uuids,
    },
  });
};

const genderize = (apollo, exclude, noStrictMatching, uuids) => {
  return apollo.mutate({
    mutation: GENDERIZE,
    variables: {
      uuids: uuids,
      exclude: exclude,
      noStrictMatching: noStrictMatching,
    },
  });
};

const unify = (apollo, criteria, exclude) => {
  return apollo.mutate({
    mutation: UNIFY,
    variables: {
      criteria: criteria,
      exclude: exclude,
    },
  });
};

const manageMergeRecommendation = (apollo, id, apply) => {
  return apollo.mutate({
    mutation: MANAGE_MERGE_RECOMMENDATION,
    variables: {
      recommendationId: id,
      apply: apply,
    },
  });
};

const recommendMatches = (apollo, criteria, exclude) => {
  return apollo.mutate({
    mutation: RECOMMEND_MATCHES,
    variables: {
      criteria: criteria,
      exclude: exclude,
    },
  });
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
  updateEnrollment,
  affiliate,
  genderize,
  unify,
  manageMergeRecommendation,
  recommendMatches,
};
