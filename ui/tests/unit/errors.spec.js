import GetErrorMessage from "@/plugins/errors";
import { createLocalVue } from "@vue/test-utils";

describe("Logger plugin", () => {
  const localVue = createLocalVue();
  localVue.use(GetErrorMessage);

  test("Returns GraphQL errors", () => {
    const error = {
      message: "GraphQL error: Organization 'Bitergia' already exists in the registry",
      graphQLErrors: [
        {
          extensions: { code: 2 },
          message: "Organization 'Bitergia' already exists in the registry"
        }
      ]
    }
    const errorMessage = localVue.prototype.$getErrorMessage(error);

    expect(errorMessage).toBe("Organization 'Bitergia' already exists in the registry");
  });

  test("Returns custom GraphQL errors", () => {
    const error = {
      message: "GraphQL error: Please enter valid credentials",
      graphQLErrors: [
        {
          extensions: { code: 129 },
          message: "Please enter valid credentials"
        }
      ]
    }
    const errorMessage = localVue.prototype.$getErrorMessage(error);

    expect(errorMessage).not.toBe("Please enter valid credentials");
  });

  test("Returns network errors", () => {
    const error = {
      message: "Network error: Error when attempting to fetch resource.",
      graphQLErrors: [],
      networkError: {
        message: "Error when attempting to fetch resource."
      }
    }
    const errorMessage = localVue.prototype.$getErrorMessage(error);

    expect(errorMessage).toBe("Error when attempting to fetch resource.");
  });
});
