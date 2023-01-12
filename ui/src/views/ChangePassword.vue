<template lang="html">
  <v-main>
    <v-card class="mx-auto mt-6 section" max-width="500" elevation="0" outlined>
      <v-card-title class="header">Password change</v-card-title>
      <v-card-subtitle v-if="showForm" class="pa-8 pb-0">
        Please enter your old password, for security’s sake, and then enter your
        new password twice so we can verify you typed it in correctly.
      </v-card-subtitle>
      <v-card-text class="pa-8">
        <v-form v-if="showForm" ref="form_change_password">
          <v-text-field
            v-model="old_password"
            label="Old password"
            name="old_password"
            type="password"
            error-count="5"
            class="mb-4"
            :error-messages="
              errors.old_password
                ? errors.old_password.map((error) => error.message)
                : []
            "
            outlined
            dense
          />
          <v-text-field
            v-model="new_password1"
            label="New password"
            name="new_password1"
            type="password"
            error-count="5"
            class="mb-4"
            :error-messages="
              errors.new_password1
                ? errors.new_password1.map((error) => error.message)
                : []
            "
            outlined
            dense
          />
          <v-text-field
            v-model="new_password2"
            label="New password confirmation"
            name="new_password2"
            type="password"
            error-count="5"
            class="mb-4"
            :error-messages="
              errors.new_password2
                ? errors.new_password2.map((error) => error.message)
                : []
            "
            outlined
            dense
          />
          <v-btn
            :disabled="!old_password || !new_password1 || !new_password2"
            color="primary"
            depressed
            @click.prevent="onSubmit"
          >
            Save
          </v-btn>
        </v-form>
        <v-alert v-else outlined type="success" text>
          Password changed successfully
        </v-alert>
      </v-card-text>
    </v-card>
  </v-main>
</template>

<script>
import Cookies from "js-cookie";

export default {
  name: "ChangePassword",
  data: () => ({
    old_password: "",
    new_password1: "",
    new_password2: "",
    errors: {},
    showForm: true,
  }),
  computed: {
    url() {
      const pathname = "/password_change/";

      if (process.env.VUE_APP_API_URL) {
        const origin = new URL(process.env.VUE_APP_API_URL).origin;

        return `${origin}${pathname}`;
      } else {
        return pathname;
      }
    },
    headers() {
      const csrftoken = Cookies.get("csrftoken");
      const authtoken = Cookies.get("sh_authtoken");
      const headers = {
        "X-CSRFToken": csrftoken,
        Authorization: `JWT ${authtoken}`,
      };

      return headers;
    },
  },
  methods: {
    onSubmit() {
      const HTMLForm = this.$refs.form_change_password.$el;
      const body = new FormData(HTMLForm);

      this.errors = {};

      fetch(this.url, {
        method: "POST",
        credentials: "include",
        headers: this.headers,
        body: body,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.errors) {
            this.errors = data.errors;
            this.$logger.error("Error changing password", data);
          } else {
            this.showForm = false;
            this.$logger.info(`Changed password for user ${data.updated}`);
          }
        });
    },
  },
};
</script>
