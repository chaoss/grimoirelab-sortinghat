import { aliasQuery } from "../utils/graphql-test-utils";

describe("Login", () => {
  beforeEach(() => {
    cy.clearCookies();
    // Intercept requests to wait for them in the tests
    cy.intercept("POST", "/api/login/").as("auth");
  });

  it("Logs in a user", () => {
    cy.visit("/");
    cy.location("pathname").should("equal", "/login");

    cy.get("[id=username]").type(Cypress.env("USERNAME"));
    cy.get("[id=password]").type(Cypress.env("PASSWORD"));
    cy.contains("button", "Log in").click();

    // Returns the user
    cy.wait("@auth")
      .its("response.body.user")
      .should("equal", Cypress.env("USERNAME"));

    // Redirects and shows the logged in user
    cy.location("pathname").should("equal", "/");
    cy.contains("header", Cypress.env("USERNAME")).should("be.visible");
  });

  it("Does not log in with wrong credentials", () => {
    cy.visit("/");
    cy.location("pathname").should("equal", "/login");

    // try logging in with invalid password
    cy.get("[id=username]").type("wrong-username");
    cy.get("[id=password]").type("wrong-password");
    cy.contains("button", "Log in").click();

    // Returns an error
    cy.wait("@auth").its("response.statusCode").should("equal", 403);

    // still on /login page plus an error is displayed
    cy.location("pathname").should("equal", "/login");
    cy.contains("Invalid credentials").should("be.visible");
  });
});

describe("Authenticated operations", () => {
  // Log in once before all tests and seed database
  before(() => {
    cy.login();
    cy.addIndividuals([
      "Test workspace",
      "Test merge 1",
      "Test merge 2",
      "Test delete 1",
      "Test delete 2",
    ]);
  });

  beforeEach(() => {
    // Set the token cookies in each test
    Cypress.Cookies.preserveOnce("sh_user", "csrftoken", "sessionid");

    // Intercept GraphQL requests to wait for them in the tests
    cy.intercept("POST", "/api/", (req) => {
      aliasQuery(req, "DeleteIdentity");
      aliasQuery(req, "GetIndividuals");
      aliasQuery(req, "Merge");
      aliasQuery(req, "unmerge");
    });
  });

  after(() => {
    // Remove individuals created by the tests
    cy.deleteIndividuals();
  });

  it("Adds individuals", () => {
    cy.visit("/");
    cy.wait("@GetIndividuals");
    cy.wait(200);

    cy.getIndividualsCount().then((count) => {
      cy.get('[data-cy="individual-add"]').click();
      cy.get("[id=name]").type("John Smith");
      cy.get("[id=source]").type("git");
      cy.contains("Save").click();

      cy.get('[data-cy="individual-add"]').click();
      cy.get("[id=email]").type("jsmith@example.com");
      cy.get("[id=source]").type("gitlab");
      cy.contains("Save").click();
      cy.wait("@GetIndividuals");
      cy.get(".v-dialog").should("not.exist");

      cy.orderBy("Last updated");

      cy.contains("tr", "John Smith").should("be.visible");
      cy.contains("tr", "jsmith@example.com").should("be.visible");
      cy.getIndividualsCount()
        .should("be.gt", count)
        .and("eq", count + 2);
    });
  });

  it("Adds individuals to workspace", () => {
    cy.visit("/");
    cy.orderBy("Last updated");

    cy.contains("tr", "Test workspace")
      .should("be.visible")
      .within(() => {
        cy.get('[aria-haspopup="menu"]').click();
      });
    cy.contains(".v-list-item", "Save in workspace").click();

    cy.get('[data-cy="workspace"]').within(() => {
      cy.contains("Test workspace").should("be.visible");
    });
  });

  it("Merges individuals", () => {
    cy.visit("/", {
      onBeforeLoad(win) {
        win.localStorage.setItem(
          "sh_workspace",
          '["fae9c66618689956f53c85da331041fd58b8da19","822d5d1cd04f9f29333bbb126e4c6c1295e4e0a5"]'
        );
      },
    });
    cy.orderBy("Last updated");

    cy.getIndividualsCount().then((count) => {
      // Select and merge individuals
      cy.contains("tr", "Test merge 1").within(() => {
        cy.get('[type="checkbox"]').click();
      });
      cy.contains("tr", "Test merge 2").within(() => {
        cy.get('[type="checkbox"]').click();
      });
      cy.get('[data-cy="merge-button"]').click();

      cy.contains(".v-overlay--active", "Merge the selected individuals?")
        .should("be.visible")
        .within(() => {
          cy.contains("Confirm").click();
        });

      // Wait for the request and the DOM update to check the count
      cy.wait("@Merge");
      cy.contains("tr", "Test merge 2").should("not.exist");
      cy.contains("tr", "Test merge 1")
        .should("have.attr", "aria-selected")
        .and("equal", "false");

      cy.getIndividualsCount()
        .should("be.lt", count)
        .and("eq", count - 1);

      // Expand merged individual and check that it has all identities
      cy.contains("tr", "Test merge 1")
        .dblclick()
        .next()
        .within(() => {
          cy.contains("Identities (2)").should("exist");
          cy.contains("Test merge 1").should("exist");
          cy.contains("Test merge 2").should("exist");
        });

      // Check it merged the individuals in the workspace
      cy.get('[data-cy="workspace"]').within(() => {
        cy.contains("Test merge 2").should("not.exist");
        cy.contains(".v-card", "Test merge 1")
          .should("exist")
          .within(() => {
            cy.get('[data-cy="expand-button"]').click();
          });
      });

      // Check if the information in the card is updated
      cy.get(".v-menu").within(() => {
        cy.contains("Identities (2)").should("exist");
        cy.contains("Test merge 1").should("exist");
        cy.contains("Test merge 2").should("exist");
      });
    });
  });

  it("Splits identities", () => {
    cy.visit("/");
    cy.orderBy("Last updated");
    cy.wait("@GetIndividuals");

    cy.getIndividualsCount().then((count) => {
      cy.contains("tr", "Test merge 1")
        .dblclick()
        .next()
        .within(() => {
          // Split the individuals merged in the previous test
          cy.contains("Identities (2)").should("exist");
          cy.contains("Test merge 1").should("exist");
          cy.contains("Test merge 2").should("exist");
          cy.contains("Split all").click();
          cy.wait("@unmerge");
          cy.wait("@GetIndividuals");
        });

      cy.contains("tr", "Test merge 1")
        .dblclick()
        .next()
        .within(() => {
          // Check that the expanded individual now has one identity
          cy.contains("Identities (1)").should("exist");
          cy.contains("Test merge 1").should("exist");
          cy.contains("Test merge 2").should("not.exist");
        });

      cy.getIndividualsCount()
        .should("be.gt", count)
        .and("eq", count + 1);
    });

    // Should have added all the split individuals to the workspace
    cy.get('[data-cy="workspace"]').within(() => {
      cy.contains(".v-card", "Test merge 1").should("be.visible");
      cy.contains(".v-card", "Test merge 2")
        .should("be.visible")
        .within(() => {
          cy.get('[data-cy="expand-button"]').click();
        });
    });

    // The information in the card is updated
    cy.get(".v-menu").within(() => {
      cy.contains("Identities (1)").should("exist");
      cy.contains("Test merge 2").should("exist");
      cy.contains("Test merge 1").should("not.exist");
    });
  });

  it("Deletes individuals", () => {
    cy.visit("/", {
      onBeforeLoad(win) {
        win.localStorage.setItem(
          "sh_workspace",
          '["aea15252fb9ebeca18698f5a7e8ff74cf6d9b18e","c132d513c6ac5d066a3076a5de75957d1ef422e5"]'
        );
      },
    });
    cy.orderBy("Last updated");

    cy.getIndividualsCount().then((count) => {
      // Select and delete individuals
      cy.contains("tr", "Test delete 1").within(() => {
        cy.get('[type="checkbox"]').click();
      });
      cy.contains("tr", "Test delete 2").within(() => {
        cy.get('[type="checkbox"]').click();
      });
      cy.get('[data-cy="delete-button"]').click();
      cy.contains(".v-overlay--active", "Delete the selected individuals?")
        .should("be.visible")
        .within(() => {
          cy.contains("Test delete 1").should("be.visible");
          cy.contains("Test delete 2").should("be.visible");
          cy.contains("Confirm").click();
        });

      cy.wait("@DeleteIdentity");
      cy.wait("@GetIndividuals");

      cy.contains("tr", "Test delete 1").should("not.exist");
      cy.contains("tr", "Test delete 2").should("not.exist");
      cy.getIndividualsCount().should("eq", count - 2);
    });

    // Check if it removes the individuals from workspace
    cy.get('[data-cy="workspace"]').within(() => {
      cy.contains("Test delete 1").should("not.exist");
      cy.contains("Test delete 2").should("not.exist");
    });
  });
});
