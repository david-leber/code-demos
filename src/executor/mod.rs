use anyhow::{Context, Result};
use bollard::container::{
    Config, CreateContainerOptions, RemoveContainerOptions, StartContainerOptions,
};
use bollard::exec::{CreateExecOptions, StartExecResults};
use bollard::Docker;
use futures::StreamExt;
use std::time::Instant;
use uuid::Uuid;

use crate::models::ExecutionResult;

pub struct CodeExecutor {
    docker: Docker,
    image_name: String,
}

impl CodeExecutor {
    pub fn new() -> Result<Self> {
        let docker = Docker::connect_with_local_defaults()
            .context("Failed to connect to Docker. Make sure Docker is running.")?;

        Ok(Self {
            docker,
            image_name: "coding-tutor-python:latest".to_string(),
        })
    }

    pub async fn build_image(&self) -> Result<()> {
        tracing::info!("Building Python execution image...");

        // Build the Docker image from the Dockerfile
        // In production, this would use bollard's build_image
        // For simplicity, we'll assume the image exists or can be built with docker build

        Ok(())
    }

    pub async fn execute_code(&self, code: &str, timeout_secs: u64) -> Result<ExecutionResult> {
        let start_time = Instant::now();
        let container_name = format!("student-code-{}", Uuid::new_v4());

        // Create container
        let config = Config {
            image: Some(self.image_name.clone()),
            tty: Some(false),
            attach_stdout: Some(true),
            attach_stderr: Some(true),
            cmd: Some(vec!["sleep".to_string(), timeout_secs.to_string()]),
            host_config: Some(bollard::models::HostConfig {
                memory: Some(256 * 1024 * 1024), // 256MB memory limit
                nano_cpus: Some(500_000_000),     // 0.5 CPU
                network_mode: Some("none".to_string()), // No network access
                ..Default::default()
            }),
            ..Default::default()
        };

        let container = self
            .docker
            .create_container(
                Some(CreateContainerOptions {
                    name: container_name.clone(),
                    ..Default::default()
                }),
                config,
            )
            .await
            .context("Failed to create container")?;

        // Start container
        self.docker
            .start_container(&container.id, None::<StartContainerOptions<String>>)
            .await
            .context("Failed to start container")?;

        // Execute Python code
        let exec = self
            .docker
            .create_exec(
                &container.id,
                CreateExecOptions {
                    attach_stdout: Some(true),
                    attach_stderr: Some(true),
                    cmd: Some(vec!["python3", "-c", code]),
                    ..Default::default()
                },
            )
            .await
            .context("Failed to create exec")?;

        let mut output_str = String::new();
        let mut error_str = String::new();

        if let StartExecResults::Attached { mut output, .. } =
            self.docker.start_exec(&exec.id, None).await?
        {
            while let Some(Ok(msg)) = output.next().await {
                match msg {
                    bollard::container::LogOutput::StdOut { message } => {
                        output_str.push_str(&String::from_utf8_lossy(&message));
                    }
                    bollard::container::LogOutput::StdErr { message } => {
                        error_str.push_str(&String::from_utf8_lossy(&message));
                    }
                    _ => {}
                }
            }
        }

        let execution_time_ms = start_time.elapsed().as_millis() as u64;

        // Clean up container
        self.docker
            .remove_container(
                &container.id,
                Some(RemoveContainerOptions {
                    force: true,
                    ..Default::default()
                }),
            )
            .await
            .context("Failed to remove container")?;

        let success = error_str.is_empty();

        Ok(ExecutionResult {
            success,
            output: output_str,
            error: if error_str.is_empty() { None } else { Some(error_str) },
            execution_time_ms,
        })
    }

    pub async fn execute_with_tests(&self, code: &str, test_code: &str) -> Result<ExecutionResult> {
        let combined_code = format!("{}\n\n{}", code, test_code);
        self.execute_code(&combined_code, 10).await
    }
}

impl Default for CodeExecutor {
    fn default() -> Self {
        Self::new().expect("Failed to create CodeExecutor")
    }
}
