import gql from "graphql-tag";

const GET_INDIVIDUAL_BYUUID = gql`
  query GetIndividual($uuid: String!) {
    individuals(filters: { uuid: $uuid }) {
      entities {
        mk
        identities {
          name
        }
        profile {
          id
          name
        }
      }
    }
  }
`;

const GET_INDIVIDUALS = gql`
  query GetIndividuals {
    individuals {
      entities {
        identities {
          name
          email
          username
        }
        profile {
          id
          name
        }
      }
    }
  }
`;

const getIndividualByUuid = (apollo, uuid) => {
  let response = apollo.query({
    query: GET_INDIVIDUAL_BYUUID,
    variables: {
      uuid: uuid
    }
  });
  return response;
};

const getIndividuals = apollo => {
  let response = apollo.query({ query: GET_INDIVIDUALS });
  return response;
};

export { getIndividuals, getIndividualByUuid };
