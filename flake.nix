{
  description = "Application packaged using poetry2nix";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.poetry2nix = {
    url = "github:nix-community/poetry2nix";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    {
      # Nixpkgs overlay providing the application
      overlay = nixpkgs.lib.composeManyExtensions [
        poetry2nix.overlay
        (final: prev: {
          # The application
          aggv2sub = prev.poetry2nix.mkPoetryApplication {
            projectDir = ./.;
            overrides = prev.poetry2nix.overrides.withDefaults (
              pyfinal: pyprev: {
                starlette = pyprev.starlette.overrideAttrs (
                  old: {
                    nativeBuildInputs = old.nativeBuildInputs ++ [ prev.python3Packages.hatchling ];
                  }
                );
              }
            );
          };
        })
      ];
    } // (flake-utils.lib.eachSystem ["x86_64-linux"] (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlay ];
        };
        packageName = "aggv2sub";
      in
      {
        apps.${packageName} = pkgs.${packageName};

        defaultApp = pkgs.${packageName};

        packages.${packageName} = pkgs.${packageName};

        defaultPackage = pkgs.${packageName};

        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            (python310.withPackages (ps: with ps; [ poetry ]))
          ];
          # shellHook = ''
            # poetry shell
          # '';
        };
      }));
}
