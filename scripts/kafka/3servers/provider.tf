provider "google" {
  project = "thesis-387607"
  region  = "us-central1"
  credentials = file("./service-account-key.json")
}
