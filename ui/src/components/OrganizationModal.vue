<template>
  <v-dialog v-model="isOpen" persistent max-width="400px">
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
          <v-row v-for="(domain, index) in form.domains" :key="index">
            <v-col cols="10">
              <v-text-field
                v-model="form.domains[index]"
                label="Domain"
                hide-details
                outlined
                dense
              />
            </v-col>
            <v-col cols="2" class="pt-3">
              <v-btn icon color="primary" @click="removeDomain(index)">
                <v-icon color="primary">mdi-delete</v-icon>
              </v-btn>
            </v-col>
          </v-row>
          <v-row class="pl-3 mt-2">
            <v-btn text small left outlined color="primary" @click="addInput">
              <v-icon small color="primary">mdi-plus-circle-outline</v-icon>
              Add domain
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
export default {
  name: "OrganizationModal",
  props: {
    addDomain: {
      type: Function,
      required: true
    },
    deleteDomain: {
      type: Function,
      required: true
    },
    addOrganization: {
      type: Function,
      required: true
    },
    isOpen: {
      type: Boolean,
      required: false,
      default: false
    },
    organization: {
      type: String,
      required: false
    },
    domains: {
      type: Array,
      required: false,
      default: () => [""]
    }
  },
  data() {
    return {
      form: {
        name: "",
        domains: [""]
      },
      errorMessage: "",
      savedData: {
        name: undefined,
        domains: []
      }
    };
  },
  methods: {
    removeDomain(index) {
      this.form.domains.splice(index, 1);
    },
    async onSave() {
      if (!this.savedData.name) {
        try {
          const response = await this.addOrganization(this.form.name);
          if (response && !response.error) {
            this.savedData.name = this.form.name;
            this.$logger.debug(`Added organization ${this.form.name}`);
            if (
              this.form.domains.length === 0 &&
              this.savedData.domains.length === 0
            ) {
              this.closeModal();
              this.$emit("updateOrganizations");
              return;
            } else {
              this.handleDomains();
            }
          }
        } catch (error) {
          this.errorMessage = this.$getErrorMessage(error);
        }
      } else {
        this.handleDomains();
      }
    },
    closeModal() {
      this.errorMessage = "";
      this.$emit("update:isOpen", false);
    },
    async handleDomains() {
      const newDomains = this.form.domains.filter(
        domain => domain.length > 0 && !this.savedData.domains.includes(domain)
      );
      const deletedDomains = this.savedData.domains.filter(
        domain => domain.length > 0 && !this.form.domains.includes(domain)
      );
      try {
        const responseNew = await Promise.all(
          newDomains.map(domain =>
            this.addOrganizationDomain(domain, this.form.name)
          )
        );
        const responseDeleted = await Promise.all(
          deletedDomains.map(domain => this.deleteOrganizationDomain(domain))
        );
        if (responseNew || responseDeleted) {
          this.closeModal();
          this.$emit("updateOrganizations");
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(`Error updating domains: ${error}`, {
          organization: this.form.name,
          newDomains,
          deletedDomains
        });
      }
    },
    async addOrganizationDomain(domain, organization) {
      const response = await this.addDomain(domain, organization);
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
      const response = await this.deleteDomain(domain);
      if (response) {
        this.$logger.debug(`Deleted domain ${domain}`);
        return response;
      }
    },
    addInput() {
      this.form.domains.push("");
    }
  },
  watch: {
    isOpen(value) {
      if (value) {
        Object.assign(this.savedData, {
          name: this.organization,
          domains: this.domains.map(domain => domain)
        });
        Object.assign(this.form, {
          name: this.organization || "",
          domains: this.domains.map(domain => domain)
        });
      } else {
        Object.assign(this.form, { name: "", domains: [""] });
        Object.assign(this.savedData, { name: undefined, domains: [""] });
      }
    }
  }
};
</script>
