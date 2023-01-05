const API_URL = Cypress.env("API_URL") || "/api/";
let uuids = [
  "8cadc67173d8293b8f9ddeb38bffe7900531d26d",
  "a371500fae13151b4e3184e98ee8ffc4cfe27097"
];

Cypress.Commands.add("login", () => {
  // Get and save the CRSF token
  cy.intercept("GET", API_URL).as("tokenCheck");
  cy.visit("/");
  cy.wait("@tokenCheck");
  cy.getCookie("csrftoken")
    .should("exist")
    .as("csrfToken");

  cy.get("@csrfToken").then(csrfToken => {
    // Login using the GraphQL mutation
    cy.request({
      method: "POST",
      url: API_URL,
      body: {
        operationName: "tokenAuth",
        query: `mutation tokenAuth($username: String!, $password: String!) {
          tokenAuth(username: $username, password: $password) {
            token
          }}`,
        variables: {
          username: Cypress.env("USERNAME"),
          password: Cypress.env("PASSWORD")
        }
      },
      headers: {
        "X-CSRFTOKEN": csrfToken.value
      }
    })
      .its("body.data.tokenAuth.token")
      .then(authToken => {
        cy.setCookie("sh_authtoken", authToken);
      });
  });

  cy.getCookie("sh_authtoken").should("exist");
  cy.getCookie("csrftoken").should("exist");
});

Cypress.Commands.add("orderBy", option => {
  cy.contains('[aria-haspopup="listbox"]', "Order by").click();
  cy.contains("[role='option']", option).click({ force: true });
  cy.wait("@GetIndividuals");
  cy.wait(500);
});

Cypress.Commands.add("addIndividuals", individuals => {
  cy.getCookie("csrftoken").then(csrfToken => {
    cy.getCookie("sh_authtoken").then(authToken => {
      // Add individual using the GraphQL mutation
      individuals.forEach(individual => {
        cy.request({
          method: "POST",
          url: API_URL,
          body: {
            operationName: "addIdentity",
            query: `mutation addIdentity($name: String) {
              addIdentity(name: $name, source: "git") {
                uuid
              }}`,
            variables: {
              name: individual
            }
          },
          headers: {
            "X-CSRFTOKEN": csrfToken.value,
            Authorization: `JWT ${authToken.value}`
          }
        }).then(response => {
          if (response.body.data.addIdentity) {
            uuids.push(response.body.data.addIdentity.uuid);
          }
        });
      });
    });
  });
});

Cypress.Commands.add("deleteIndividuals", () => {
  cy.getCookie("csrftoken").then(csrfToken => {
    cy.getCookie("sh_authtoken").then(authToken => {
      uuids.forEach(uuid => {
        cy.request({
          method: "POST",
          url: API_URL,
          body: {
            operationName: "DeleteIdentity",
            query: `mutation DeleteIdentity($uuid: String) {
              deleteIdentity(uuid: $uuid) {
                uuid
              }}`,
            variables: {
              uuid: uuid
            }
          },
          headers: {
            "X-CSRFTOKEN": csrfToken.value,
            Authorization: `JWT ${authToken.value}`
          }
        });
      });
    });
  });
});

Cypress.Commands.add("getIndividualsCount", () => {
  cy.get('[data-cy="individual-counter"]')
    .invoke("text")
    .then(parseFloat);
});

Cypress.Commands.add("addToWorkspace", individuals => {
  individuals.forEach(name => {
    cy.contains("tr", name)
      .should("be.visible")
      .within(() => {
        cy.get('[aria-haspopup="true"]').click();
      });
    cy.contains(
      '.menuable__content__active [role="menuitem"]',
      "Save in workspace"
    )
      .should("be.visible")
      .click({ force: true });
    cy.get('[data-cy="workspace"]').within(() => {
      cy.contains(name).should("be.visible");
    });
  });
});
