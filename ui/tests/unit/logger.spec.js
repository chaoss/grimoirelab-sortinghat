import Logger from "@/plugins/logger";
import { createLocalVue } from "@vue/test-utils";

describe("Logger plugin", () => {
  const localVue = createLocalVue();
  localVue.use(Logger);

  // Mock console functions to prevent the tests from printing the messages
  jest.spyOn(console, "error").mockImplementation(jest.fn());
  jest.spyOn(console, "debug").mockImplementation(jest.fn());
  jest.spyOn(console, "log").mockImplementation(jest.fn());
  jest.spyOn(console, "info").mockImplementation(jest.fn());
  jest.spyOn(console, "warn").mockImplementation(jest.fn());

  afterEach(() => {
    jest.clearAllMocks();
  });

  test("Logs error message", () => {
    localVue.prototype.$logger.error("Test error message");

    expect(console.error.mock.calls.length).toBe(1);
    expect(console.error.mock.calls[0][0]).toBe("Test error message");
  });

  test("Logs debug message", () => {
    localVue.prototype.$logger.debug("Test debug message");

    expect(console.debug.mock.calls.length).toBe(1);
    expect(console.debug.mock.calls[0][0]).toBe("Test debug message");
  });

  test("Logs default message", () => {
    localVue.prototype.$logger.log("Test default message");

    expect(console.log.mock.calls.length).toBe(1);
    expect(console.log.mock.calls[0][0]).toBe("Test default message");
  });

  test("Logs info message", () => {
    localVue.prototype.$logger.info("Test info message");

    expect(console.info.mock.calls.length).toBe(1);
    expect(console.info.mock.calls[0][0]).toBe("Test info message");
  });

  test("Logs warning message", () => {
    localVue.prototype.$logger.warn("Test warning message");

    expect(console.warn.mock.calls.length).toBe(1);
    expect(console.warn.mock.calls[0][0]).toBe("Test warning message");
  });
})
