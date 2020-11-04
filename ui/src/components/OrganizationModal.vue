<template>
  <v-dialog v-model="isOpen" persistent max-width="450px">
    <v-card class="pa-6">
      <v-card-title>
        <span class="headline">Add organization</span>
      </v-card-title>
      <form>
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-text-field label="Name" v-model="form.name" filled required />
            </v-col>
          </v-row>
          <v-row class="pl-4">
            <span class="title font-weight-regular pl-16">Domains</span>
          </v-row>
          <v-list>
            <v-list-item v-for="(domain, index) in form.domains" :key="index">
              <v-list-item-content>
                <v-list-item-title v-text="domain" />
              </v-list-item-content>
              <v-list-item-action>
                <v-btn icon @click="removeDomain(index)">
                  <v-icon small color="primary">mdi-delete</v-icon>
                </v-btn>
              </v-list-item-action>
            </v-list-item>
          </v-list>
          <v-row class="flex-row align-center">
            <v-col cols="9">
              <v-text-field
                v-model="activeDomain"
                label="Domain"
                filled
                @keyup.enter="saveDomain"
              />
            </v-col>
            <v-col cols="2">
              <v-btn
                block
                text
                color="primary"
                :disabled="activeDomain.length === 0"
                @click="saveDomain"
              >
                Add
              </v-btn>
            </v-col>
          </v-row>
          <v-alert v-if="errorMessage" text type="error">
            {{ errorMessage }}
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue darken-1" text @click.prevent="onCancel">
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
    addOrganization: {
      type: Function,
      required: true
    },
    isOpen: {
      type: Boolean,
      required: false,
      default: false
    }
  },
  data() {
    return {
      form: {
        name: "",
        domains: []
      },
      activeDomain: "",
      errorMessage: ""
    };
  },
  methods: {
    saveDomain() {
      this.form.domains.push(this.activeDomain);
      this.activeDomain = "";
    },
    removeDomain(index) {
      this.form.domains.splice(index, 1);
    },
    async onSave() {
      try {
        const response = await this.addOrganization(this.form.name);
        if (response) {
          if (this.form.domains.length === 0) {
            this.errorMessage = "";
            Object.assign(this.form, { name: "", domains: [] });
            this.$emit("update:isOpen", false);
            this.$emit("updateOrganizations");
            return;
          }
          const domainsResponse = await Promise.all(
            this.form.domains.map(domain =>
              this.addOrganizationDomain(domain, this.form.name)
            )
          );
          if (domainsResponse) {
            Object.assign(this.form, { name: "", domains: [] });
            this.errorMessage = "";
            this.$emit("update:isOpen", false);
            this.$emit("updateOrganizations");
          }
        }
      } catch (error) {
        this.errorMessage = error;
      }
    },
    onCancel() {
      Object.assign(this.form, { name: "", domains: [] });
      this.errorMessage = "";
      this.$emit("update:isOpen", false);
    },
    async addOrganizationDomain(domain, organization) {
      try {
        const response = await this.addDomain(domain, organization);
        if (response) {
          return response;
        }
      } catch (error) {
        this.errorMessage = error;
      }
    }
  }
};
</script>
