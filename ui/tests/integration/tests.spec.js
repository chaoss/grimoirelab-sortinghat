const { argv } = require("yargs");

const DEFAULT_URL = "http://localhost:8080";
const TIMEOUT = 10000;

const getURL = (url) => {
  if (url) {
    if (url.slice(-1) === "/") {
      return url.slice(0, -1)
    } else {
      return url;
    }
  } else {
    return DEFAULT_URL;
  }
};

const BASE_URL = getURL(argv.url);

async function orderIndividuals() {
  const selector = await page.waitForSelector(".select .v-input__slot");
  await selector.evaluate(el => el.click());
  const option = await page.waitForSelector(".v-list-item", {
    text: "Last updated",
    visible: true,
    timeout: TIMEOUT
  });
  await option.evaluate(el => el.click());
  await page.waitForSelector("tr[draggable]", { text: "John Smith" });
  return await page.waitForSelector("tr[draggable]", {
    text: "jsmith@example.com"
  });
};

describe("Login", () => {
  it("Does not log in with wrong credentials", async () => {
    await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle0" });

    await page.type("#username", "testusername");
    await page.type("#password", "wrongpassword");
    await expect(page).toClick('button', { text: "Log in" });

    await expect(page).toMatch("Invalid credentials");
    await expect(page.url()).toBe(`${BASE_URL}/login`);
  });

  it("Logs in a user", async () => {
    await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle0" });

    await page.type("#username", "testusername");
    await page.type("#password", "password");
    await expect(page).toClick('button', { text: "Log in" });
    await page.waitForNavigation();

    await expect(page.url()).toBe(`${BASE_URL}/`);
  });
});

describe("Operations", () => {
  it("Adds individuals", async () => {
    await page.goto(BASE_URL, { waitUntil: "networkidle0" });
    await page.setDefaultTimeout(TIMEOUT);

    // Get the number of individuals
    const counter = await page.$(".individuals .v-chip__content");
    const beforeCount = await counter.evaluate(el => parseInt(el.textContent));

    // Add individuals
    await page.click(".js-add-individual");
    await page.type("#name", "John Smith");
    await page.type("#source", "git");
    await expect(page).toClick("button", { text: "Save" });
    await page.waitForTimeout(1000);

    await page.click(".js-add-individual");
    await page.type("#email", "jsmith@example.com");
    await page.type("#source", "gitlab");
    await expect(page).toClick("button", { text: "Save" });
    await page.waitForTimeout(1000);

    await orderIndividuals();

    await expect(page).toMatch("John Smith");
    await expect(page).toMatch("jsmith@example.com");

    const afterCount = await counter.evaluate(el => parseInt(el.textContent));
    await expect(afterCount).toBe(beforeCount + 2);
  });

  it("Merges individuals", async () => {
    await page.goto(BASE_URL, { waitUntil: "networkidle0" });
    await page.setDefaultTimeout(TIMEOUT);

    // Get the number of individuals before the merge
    const counter = await page.$(".individuals .v-chip__content");
    const beforeCount = await counter.evaluate(el => parseInt(el.textContent));

    await orderIndividuals();

    // Merge individuals
    await page.setDragInterception(true);
    let individuals = await page.$$("tr[draggable]");
    await individuals[0].evaluate(el => el.click());
    await individuals[1].evaluate(el => el.click());
    await page.waitForTimeout(500);
    await expect(page).toClick("button:not([disabled])", { text: "Merge" });
    await expect(page).toMatch("Merge the selected items?", {
      timeout: TIMEOUT
    });
    const button = await page.waitForSelector("#confirm", {
      visible: true,
      timeout: TIMEOUT
    });
    await button.evaluate(el => el.click());
    await page.waitForTimeout(1000);

    const afterCount = await counter.evaluate(el => parseInt(el.textContent));
    await expect(afterCount).toBe(beforeCount - 1);

    // Double click first individual to expand info
    individuals = await page.$$("tr[draggable]");
    const clickArea = await individuals[0].$(".text-right");
    await clickArea.click({ clickCount: 1, delay: 100 });
    await clickArea.click({ clickCount: 2, delay: 100 });

    await expect(page).toMatch("Identities (2)", { timeout: TIMEOUT });
  });

  it("Deletes individuals", async () => {
    await page.goto(BASE_URL, { waitUntil: "networkidle0" });
    await page.setDefaultTimeout(TIMEOUT);

    // Get the number of individuals before deleting
    const counter = await page.$(".individuals .v-chip__content");
    const beforeCount = await counter.evaluate(el => parseInt(el.textContent));

    await orderIndividuals();

    // Delete individual
    const individual = await page.$("tr[draggable] .text-right");
    await individual.click();
    await page.waitForTimeout(500);
    await expect(page).toClick("button", { text: "Delete" });
    await expect(page).toMatch("Delete the selected items?", {
      timeout: TIMEOUT
    });
    const button = await page.waitForSelector("#confirm", {
      visible: true,
      timeout: TIMEOUT
    });
    await button.evaluate(el => el.click());
    await page.waitForTimeout(1000);

    const afterCount = await counter.evaluate(el => parseInt(el.textContent));
    await expect(afterCount).toBe(beforeCount - 1);
  });
});
