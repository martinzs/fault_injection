#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>

int main(int argc, char *args[])
{
    char dirs[][4] = {"aaa", "bbb"};
    for (int i = 0; i < 2; i++)
    {
        sleep(3);
        if (mkdir(dirs[i], 0777) == -1)
        {
            perror("mkdir: ");
        }
        else
        {
            if (fprintf(stdout, "Dir %s created\n", dirs[i]) < 0)
                perror("Write: ");
            else
                if (fflush(stdout) == EOF)
                    perror("Write: ");
        }

        sleep(3);
        if (chmod(dirs[i], S_IRUSR) == -1)
        {
            perror("chmod: ");
        }
        else
        {
            if (fprintf(stdout, "Change permission: read owner\n") < 0)
                perror("Write: ");
            else
                if (fflush(stdout) == EOF)
                    perror("Write: ");
        }

        sleep(3);
        if (chmod(dirs[i], S_IRGRP) == -1)
        {
            perror("chmod: ");
        }
        else
        {
            if (fprintf(stdout, "Change permission: read group\n") < 0)
                perror("Write: ");
            else
                if (fflush(stdout) == EOF)
                    perror("Write: ");
        }

        sleep(3);
        if (chmod(dirs[i], S_IROTH) == -1)
        {
            perror("chmod: ");
        }
        else
        {
            if (fprintf(stdout, "Change permission: read other\n") < 0)
                perror("Write: ");
            else
                if (fflush(stdout) == EOF)
                    perror("Write: ");
        }
        
        sleep(3);
        if (rmdir(dirs[i]) == -1)
        {
            perror("rmdir: ");
        }
        else
        {
            if (fprintf(stdout, "Removed %s\n", dirs[i]) < 0)
                perror("Write: ");
            else
                if (fflush(stdout) == EOF)
                    perror("Write: ");
        }
    }
}
