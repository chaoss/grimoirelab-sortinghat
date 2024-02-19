<template>
  <v-dialog v-model="isOpen" persistent max-width="440px">
    <v-card class="section">
      <v-card-title class="header">
        <span class="title">
          {{ organization ? "Edit" : "Add" }} organization
        </span>
      </v-card-title>
      <form>
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-text-field
                label="Name"
                v-model="form.name"
                :disabled="!!savedData.name"
                outlined
                dense
              />
            </v-col>
          </v-row>
          <v-row class="pl-4">
            <span class="subheader">Domains</span>
          </v-row>
          <v-row
            v-for="(domain, index) in form.domains"
            :key="index"
            class="align-bottom"
          >
            <v-col cols="6">
              <v-text-field
                v-model="form.domains[index].domain"
                label="Domain"
                hide-details
                outlined
                dense
              />
            </v-col>
            <v-col cols="4">
              <v-checkbox
                v-model="form.domains[index].isTopDomain"
                label="Top domain"
                dense
                hide-details
              />
            </v-col>
            <v-col cols="2" class="pt-3">
              <v-btn icon color="primary" @click="removeDomain(index)">
                <v-icon color="primary">mdi-delete</v-icon>
              </v-btn>
            </v-col>
          </v-row>
          <v-row class="pl-3 mt-2 mb-4">
            <v-btn text small outlined color="primary" @click="addInput">
              <v-icon small left color="primary">
                mdi-plus-circle-outline
              </v-icon>
              Add domain
            </v-btn>
          </v-row>
          <v-row class="pl-4">
            <span class="subheader">Aliases</span>
          </v-row>
          <v-row
            v-for="(alias, index) in form.aliases"
            :key="`alias-${index}`"
            class="align-bottom"
          >
            <v-col cols="10">
              <v-text-field
                v-model="form.aliases[index]"
                label="Alias"
                hide-details
                outlined
                dense
              />
            </v-col>
            <v-col cols="2" class="pt-3">
              <v-btn
                icon
                color="primary"
                @click="form.aliases.splice(index, 1)"
              >
                <v-icon color="primary">mdi-delete</v-icon>
              </v-btn>
            </v-col>
          </v-row>
          <v-row class="pl-3 mt-2">
            <v-btn
              text
              small
              outlined
              color="primary"
              @click="form.aliases.push('')"
            >
              <v-icon small left color="primary">
                mdi-plus-circle-outline
              </v-icon>
              Add alias
            </v-btn>
          </v-row>
          <v-alert v-if="errorMessage" text type="error" class="mt-3">
            {{ errorMessage }}
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary darken-1" text @click.prevent="closeModal">
            Cancel
          </v-btn>
          <v-btn
            depressed
            color="primary"
            :disabled="form.name.length === 0"
            @click.prevent="onSave"
          >
            Save
          </v-btn>
        </v-card-actions>
      </form>
    </v-card>
  </v-dialog>
</template>

<script>
const emptyDomain = {
  domain: "",
  isTopDomain: false,
};

export default {
  name: "OrganizationModal",
  props: {
    addDomain: {
      type: Function,
      required: true,
    },
    deleteDomain: {
      type: Function,
      required: true,
    },
    addOrganization: {
      type: Function,
      required: true,
    },
    isOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
    organization: {
      type: String,
      required: false,
    },
    domains: {
      type: Array,
      required: false,
      default: () => [],
    },
    aliases: {
      type: Array,
      required: false,
      default: () => [""],
    },
    addAlias: {
      type: Function,
      required: true,
    },
    deleteAlias: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      form: {
        name: "",
        domains: [emptyDomain],
        aliases: [""],
      },
      errorMessage: "",
      savedData: {
        name: undefined,
        domains: [],
      },
    };
  },
  methods: {
    removeDomain(index) {
      this.form.domains.splice(index, 1);
    },
    async onSave() {
      this.errorMessage = "";
      if (!this.savedData.name) {
        try {
          const response = await this.addOrganization(this.form.name);
          if (response && !response.error) {
            this.savedData.name = this.form.name;
            this.$logger.debug(`Added organization ${this.form.name}`);
            if (
              this.form.domains.length === 0 &&
              this.savedData.domains.length === 0 &&
              this.form.aliases.length === 0 &&
              this.savedData.aliases.length === 0
            ) {
              this.closeModal();
              this.$emit("updateOrganizations");
              return;
            } else {
              await this.handleDomains();
              await this.handleAliases();
              if (!this.errorMessage) {
                this.closeModal();
              }
            }
          }
        } catch (error) {
          this.errorMessage = this.$getErrorMessage(error);
        }
      } else {
        await this.handleDomains();
        await this.handleAliases();
        if (!this.errorMessage) {
          this.closeModal();
        }
      }
    },
    closeModal() {
      this.errorMessage = "";
      this.$emit("update:isOpen", false);
    },
    async handleDomains() {
      const newDomains = this.form.domains.filter(
        (domain) =>
          domain.domain.length > 0 &&
          !this.savedData.domains.some(
            (savedDomain) => savedDomain.domain === domain.domain
          )
      );
      const deletedDomains = this.savedData.domains.filter(
        (domain) =>
          domain.domain.length > 0 &&
          !this.form.domains.some(
            (savedDomain) => savedDomain.domain === domain.domain
          )
      );
      try {
        const responseNew = await Promise.all(
          newDomains.map((domain) =>
            this.addOrganizationDomain(domain, this.form.name)
          )
        );
        const responseDeleted = await Promise.all(
          deletedDomains.map((domain) => this.deleteOrganizationDomain(domain))
        );
        if (responseNew || responseDeleted) {
          this.$emit("updateOrganizations");
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(`Error updating domains: ${error}`, {
          organization: this.form.name,
          newDomains,
          deletedDomains,
        });
      }
    },
    async addOrganizationDomain(domain, organization) {
      const response = await this.addDomain(
        domain.domain,
        domain.isTopDomain,
        organization
      );
      if (response && !response.error) {
        this.savedData.domains.push(domain);
        this.$logger.debug("Added domain", { domain, organization });
        return response;
      } else if (response.errors) {
        this.$logger.error(
          `Error adding domain: ${response.errors[0].message}`,
          { domain, organization }
        );
      }
    },
    async deleteOrganizationDomain(domain) {
      const response = await this.deleteDomain(domain.domain);
      if (response) {
        this.$logger.debug(`Deleted domain ${domain.domain}`);
        return response;
      }
    },
    addInput() {
      this.form.domains.push({ ...emptyDomain });
    },
    async handleAliases() {
      const newAliases = this.form.aliases.filter(
        (alias) =>
          alias.length > 0 &&
          !this.savedData.aliases.some((savedAlias) => savedAlias === alias)
      );
      const deletedAliases = this.savedData.aliases.filter(
        (alias) =>
          alias.length > 0 &&
          !this.form.aliases.some((savedAlias) => savedAlias === alias)
      );
      try {
        const responseNew = await Promise.all(
          newAliases.map((alias) =>
            this.addOrganizationAlias(alias, this.form.name)
          )
        );
        const responseDeleted = await Promise.all(
          deletedAliases.map((alias) => this.deleteOrganizationAlias(alias))
        );
        if (responseNew || responseDeleted) {
          this.$emit("updateOrganizations");
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(`Error updating aliases: ${error}`, {
          organization: this.form.name,
          newAliases,
          deletedAliases,
        });
      }
    },
    async addOrganizationAlias(alias, organization) {
      const response = await this.addAlias(alias, organization);
      if (response && !response.error) {
        this.savedData.aliases.push(alias);
        this.$logger.debug(
          `Added alias ${alias} to organization ${organization}`
        );
        return response;
      } else if (response.errors) {
        this.$logger.error(
          `Error adding alias: ${response.errors[0].message}`,
          { alias, organization }
        );
      }
    },
    async deleteOrganizationAlias(alias) {
      const response = await this.deleteAlias(alias);
      if (response) {
        this.$logger.debug(`Deleted alias ${alias}`);
        return response;
      }
    },
  },
  watch: {
    isOpen(value) {
      if (value) {
        Object.assign(this.savedData, {
          name: this.organization,
          domains: this.domains.map((domain) => ({ ...domain })),
          aliases: this.aliases.map((alias) => alias),
        });
        Object.assign(this.form, {
          name: this.organization || "",
          domains: this.domains.map((domain) => ({ ...domain })),
          aliases: this.aliases.map((alias) => alias),
        });
      } else {
        Object.assign(this.form, {
          name: "",
          domains: [{ ...emptyDomain }],
          aliases: [""],
        });
        Object.assign(this.savedData, {
          name: undefined,
          domains: [{ ...emptyDomain }],
          aliases: [""],
        });
      }
    },
  },
};
</script>
